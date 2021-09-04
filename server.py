import random
import queue
import socket
import threading

from game_data import GameData
from matrix import Matrix
from network import PORT, send_object, get_object

SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind((socket.gethostname(), PORT))


class Server:
    def __init__(self):
        self.max_game_count = 5
        self.max_player_count = 2
        self.curr_game_id = 0
        self.data_queue = queue.SimpleQueue()
        self.games_dict = {}
        self.add_new_game()

    def add_new_game(self):
        self.games_dict[self.curr_game_id] = GameData()

    def threaded_client(self, client_conn, addr, client_id):
        game_id = self.curr_game_id
        print(f"New Connection from {addr}.")
        print(f"Connection data: {client_conn}.")
        print()

        send_object(("ID", client_id), client_conn)

        if self.games_dict[game_id].player_count == 2:
            for connection in server_data.games_dict[game_id].connections:
                send_object(("Status update", "picking ships"), connection)

        while True:
            try:
                key_code, new_object = get_object(client_conn)
                self.data_queue.put((game_id, client_id, client_conn, key_code, new_object))
            except ConnectionAbortedError:
                print("Game ended. Closing Thread.")
                return
            except ConnectionResetError:
                print("Client exited the game. Closing Thread.")
                return

    def data_thread(self):
        while self.data_queue:
            game_id, client_id, client_conn, key_code, new_object = self.data_queue.get(block=True)

            if key_code == "Chat":
                for connection in server_data.games_dict[game_id].connections:
                    if connection != client_conn:
                        send_object(("Chat", new_object), connection)

            elif key_code == "New ship data":
                ship_name, is_horizontal, cursor_cell_coord = new_object
                if self.games_dict[game_id].matrixes[client_id].ship_count[ship_name] == 0:
                    continue

                self.games_dict[game_id].matrixes[client_id].create_ship(ship_name, self.games_dict[game_id].ships)
                self.games_dict[game_id].matrixes[client_id].cursor_cell_coord = cursor_cell_coord
                self.games_dict[game_id].matrixes[client_id].floating_ship.is_horizontal = is_horizontal
                self.games_dict[game_id].matrixes[client_id].update_floating_ship()

                if len(self.games_dict[game_id].matrixes[client_id].floating_ship_positions) == self.games_dict[game_id].matrixes[client_id].floating_ship.hitpoints:
                    self.games_dict[game_id].matrixes[client_id].update_ships()
                    self.games_dict[game_id].matrixes[client_id].place_ship()

            elif key_code == "Ready":
                if sum(self.games_dict[game_id].matrixes[client_id].ship_count.values()) != 0:
                    print("Incorrect ship placements!")

                elif self.games_dict[game_id].readys + 1 == self.max_player_count:
                    self.games_dict[game_id].readys = 0
                    self.games_dict[game_id].active_player_id = random.randint(0, 1)
                    for i, conn in enumerate(self.games_dict[game_id].connections):
                        send_object(("Status update", "game on"), conn)
                        send_object(("Active player", self.games_dict[game_id].active_player_id), conn)
                else:
                    self.games_dict[game_id].readys += 1

            elif key_code == "Shoot":
                if self.games_dict[game_id].active_player_id == client_id:
                    cell_coord = new_object

                    if not self.games_dict[game_id].matrixes[1 - client_id].cells_dict[cell_coord].status:
                        for connection in self.games_dict[game_id].connections:
                            if connection != client_conn:
                                send_object(("Shoot", cell_coord), connection)  # this also means your turn, unless all ships are sunk
                                break

                        self.games_dict[game_id].active_player_id = 1 - client_id
                        self.games_dict[game_id].matrixes[1 - client_id].shot_at(cell_coord)

                        turn_result = self.games_dict[game_id].matrixes[1 - client_id].cells_dict[cell_coord].status
                        send_object(("Turn result", (turn_result, cell_coord)), client_conn)
                        if turn_result == "hit":
                            if self.games_dict[game_id].matrixes[1 - client_id].cells_dict[cell_coord].ship.hitpoints == 0:
                                self.games_dict[game_id].matrixes[client_id].enemy_ship_count -= 1
                                if self.games_dict[game_id].matrixes[client_id].enemy_ship_count == 0:
                                    send_object(("Victory", None), client_conn)
                                    for connection in self.games_dict[game_id].connections:
                                        print(f"Closing connection to {connection}")
                                        connection.close()
                                    del self.games_dict[game_id]
                                    # the looser should recognise that its over, no need to send msg

                                else:
                                    send_object(("Sunk", None), client_conn)

            elif key_code == 'Exiting':
                print(f"Closing connection to {client_conn}")
                client_conn.close()
                self.games_dict[game_id].player_count -= 1
                if self.games_dict[game_id].player_count == 0:
                    del self.games_dict[game_id]

            else:
                print(f"Unknown message from client: {key_code}")


SERVER.listen(5)  # maximum number of connect requests
server_data = Server()
server_thread = threading.Thread(target=server_data.data_thread)
server_thread.start()
print()
print('[SERVER] started. Waiting for connections...')
print()


while True:  # handling new connections
    connection, address = SERVER.accept()
    SERVER.setblocking(True)  # prevents timeout
    server_data.games_dict[server_data.curr_game_id].add_player(connection)
    client_id = server_data.games_dict[server_data.curr_game_id].player_count - 1

    new_thread = threading.Thread(target=server_data.threaded_client, args=(connection, address, client_id))
    new_thread.start()

    if server_data.games_dict[server_data.curr_game_id].player_count == 2:
        server_data.curr_game_id += 1
        server_data.games_dict[server_data.curr_game_id] = GameData()
