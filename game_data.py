import socket
import threading
import time

from matrix import Matrix
from network import PORT, get_object
from ship import Ship


class GameData:
    def __init__(self, resolution=(1, 1)):
        self.connected = False
        self.socket = None
        self.player_count = 0
        self.connections = set()

        self.readys = 0
        self.status = None
        self.my_id = 0
        self.enemy_id = 1
        self.active_player_id = None

        self.ships = {}
        self.load_ships()

        self.matrixes = {}
        self.create_matrixes(resolution)

    def clear(self, resolution):
        # need to stop the thread
        self.socket = None
        self.status = None
        self.create_matrixes(resolution)

    def create_matrixes(self, resolution):
        row = col = 10
        cell_size = resolution[1] // 20
        x = resolution[0] / 2 - (row + 1) * cell_size / 2
        y = resolution[1] / 2 - (col + 1) * cell_size / 2
        for i in range(2):
            self.matrixes[i] = Matrix(x, y, row, col, cell_size)

    def update_matrix(self, resolution):
        self.matrixes[self.my_id].update(new_x=resolution[0] // 20 * 15, new_y=resolution[1] // 10, new_cell_size=resolution[1] // 40)

    def reset(self):  # i may not need this
        self.player_count = 0
        # reset the matrix

    def add_player(self, conn):
        self.player_count += 1
        self.connections.add(conn)

    def update_active_player(self, player_id, ui):
        self.active_player_id = player_id
        if player_id is None:
            ui.menus["info panel"].objects["player turn"].update_text("Game Over")
        elif self.active_player_id == self.my_id:
            ui.menus["info panel"].objects["player turn"].update_text("Your turn")
        else:  # this might never run
            ui.menus["info panel"].objects["player turn"].update_text("Enemy's turn")


    def new_game(self, ui, settings):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        thread = threading.Thread(target=self.data_thread, args=(ui, settings))
        thread.daemon = True
        thread.start()

    def load_ships(self):
        self.ships = {
            "carrier": Ship(name="carrier", hitpoints=5, matrix=[
                [None, None, None, None, None],
                [None, None, None, None, None],
                ["ship_piece_0", "ship_piece_2", "ship_piece_2", "ship_piece_2", "ship_piece_3"],
                [None, None, None, None, None],
                [None, None, None, None, None]
            ]),
            "battleship": Ship(name="battleship", hitpoints=4, matrix=[
                [None, None, None, None, None],
                [None, None, None, None, None],
                ["ship_piece_1", "ship_piece_2", "ship_piece_2", "ship_piece_3", None],
                [None, None, None, None, None],
                [None, None, None, None, None]
            ]),
            "destroyer": Ship(name="destroyer", hitpoints=3, matrix=[
                [None, None, None, None, None],
                [None, None, None, None, None],
                [None, "ship_piece_1", "ship_piece_2", "ship_piece_3", None],
                [None, None, None, None, None],
                [None, None, None, None, None]
            ]),
            "submarine": Ship(name="submarine", hitpoints=3, matrix=[
                [None, None, None, None, None],
                [None, None, None, None, None],
                [None, "ship_piece_1", "ship_piece_2", "ship_piece_3", None],
                [None, None, None, None, None],
                [None, None, None, None, None]
            ]),
            "patrol boat": Ship(name="patrol boat", hitpoints=2, matrix=[
                [None, None, None, None, None],
                [None, None, None, None, None],
                [None, "ship_piece_1", "ship_piece_3", None, None],
                [None, None, None, None, None],
                [None, None, None, None, None]
            ])
        }

    def data_thread(self, ui, settings):
        while self.status != "exiting":
            if not self.connected:
                try:
                    self.socket.connect((socket.gethostname(), PORT))
                    self.connected = True
                    print()
                    print('Connected to Server.')
                    pass
                except ConnectionRefusedError as e:
                    print(f'Server not found. - {e}.')
                    time.sleep(0.5)
                    continue
                except AttributeError:
                    if self.socket is None:
                        return

            while self.connected:
                try:
                    key_code, new_object = get_object(self.socket)

                    if key_code == "Chat":
                        ui.update_msg_objects(new_object, ui.enemy_msg_color, settings.get_resolution())
                        ui.chat_msg_num += 1

                    elif key_code == "Turn result":
                        result, cell_coord = new_object
                        self.matrixes[self.enemy_id].cells_dict[cell_coord].status = result
                        ui.menus["info panel"].objects["turn result"].update_text(result)

                    elif key_code == "Shoot":
                        self.matrixes[self.my_id].shot_at(new_object)
                        if self.matrixes[self.my_id].my_ship_count == 0:
                            self.status = "exiting"
                            ui.menus["info panel"].objects["turn result"].update_text("You lost!")
                            self.update_active_player(None, ui)
                        else:
                            self.update_active_player(self.my_id, ui)

                    elif key_code == "Sunk":
                        self.matrixes[self.my_id].enemy_ship_count -= 1
                        ui.menus["info panel"].objects["turn result"].update_text("Ship sunk!")

                    elif key_code == "Victory":
                        self.status = "exiting"
                        ui.menus["info panel"].objects["turn result"].update_text("You won!")
                        self.update_active_player(None, ui)
                        # play a fireworks sound effect

                    elif key_code == "ID":
                        self.my_id = new_object
                        self.enemy_id = 1 - self.my_id

                    elif key_code == "Status update":
                        self.status = new_object
                        if self.status == "game on":
                            self.update_matrix(settings.get_resolution())

                    elif key_code == "Active player":
                        self.update_active_player(new_object, ui)

                    else:
                        print(f"Unknown message from server: {key_code}")

                except ConnectionResetError as e:
                    print(f'Connection lost to SERVER. - {e}')
                    self.connected = False
                    self.socket.close()
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    break
            time.sleep(1)