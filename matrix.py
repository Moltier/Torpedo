import pygame
from cell import Cell


class Matrix:
    def __init__(self, x, y, row, col, cell_size):
        self.x = x
        self.y = y
        self.row = row
        self.col = col
        self.cell_size = cell_size
        self.cells_dict = {}
        self.cursor_cell_coord = ()
        self.prev_cursor_cell_coord = (-1, -1)

        self.floating_ship = None
        self.floating_ship_positions = []
        self.ship_count = {}
        self.create_ship_data()
        self.my_ship_count = sum(self.ship_count.values())
        self.enemy_ship_count = self.my_ship_count
        # self.ship_value = 0

        self.create_matrix()

        self.grid_color = (0, 255, 0)
        # 2 matrixot kéne elhelyezni, és méretezni
        # először csak 1et kell, amíg megy a tervezés
        # aztán jön a kövi fázis, amikor a saját lehetne piciben bal felül megjelenítve
        # míg a lövöldöző tábla középen nagyban
        self.images = {}  # ez lehet inkább a ui-ba kéne
        self.update(new_cell_size=self.cell_size)

    def create_ship_data(self):
        self.ship_count = {"carrier": 0,
                           "battleship": 0,
                           "destroyer": 0,
                           "submarine": 0,
                           "patrol boat": 1}  # should be 1,1,2,2,3 or 1,1,1,1,1

    def create_matrix(self):
        for row in range(self.row):
            for col in range(self.col):
                # first row and col with letters and nums
                self.cells_dict[(row, col)] = Cell()

    def update(self, new_x=None, new_y=None, new_cell_size=None):
        if new_x:
            self.x = new_x
        if new_y:
            self.y = new_y
        if new_cell_size:
            self.cell_size = new_cell_size
            for img_name in ("ship", "hit", "miss"):
                self.images[img_name] = pygame.transform.scale(
                    pygame.image.load(f"Images/{img_name}.png"), (self.cell_size, self.cell_size)).convert()
                self.images[img_name].set_colorkey((255, 255, 255))

            for img_name in (
                    "ship_piece_0_h", "ship_piece_1_h", "ship_piece_2_h", "ship_piece_3_h",
                    "ship_piece_0_v", "ship_piece_1_v", "ship_piece_2_v", "ship_piece_3_v"):
                self.images[img_name] = pygame.transform.scale(
                    pygame.image.load(f"Images/{img_name}.png"), (self.cell_size, self.cell_size)).convert()
                self.images[img_name].set_colorkey((255,255,255))

    def shot_at(self, coord):
        if self.cells_dict[coord].ship:
            self.cells_dict[coord].status = "hit"
            self.cells_dict[coord].ship.hitpoints -= 1
            if self.cells_dict[coord].ship.hitpoints == 0:
                self.my_ship_count -= 1
        else:
            self.cells_dict[coord].status = "miss"


    def pos_in_matrix(self, pos):
        if self.x < pos[0] < (self.x + self.col * self.cell_size) \
                and self.y < pos[1] < (self.y + self.row * self.cell_size):
            return True
        return False

    def update_cursor_cell_coor(self, mouse_pos):
        if self.pos_in_matrix(mouse_pos):
            self.cursor_cell_coord = self.get_cell_coord(mouse_pos)

    def create_ship(self, ship_name, ships):
        self.clear_floating_ship()
        self.floating_ship = ships[ship_name].__copy__()
        self.cursor_cell_coord = (self.col // 2, self.row // 2)
        self.update_floating_ship()
        self.prev_cursor_cell_coord = self.cursor_cell_coord

    def update_ships(self):
        # self.ship_value += self.floating_ship.hitpoints
        self.ship_count[self.floating_ship.name] -= 1

    def clear_floating_ship(self):
        for coord in self.floating_ship_positions:
            self.cells_dict[coord].ship_piece_name = None
        self.floating_ship_positions.clear()

    def update_floating_ship(self):
        self.clear_floating_ship()

        # update cells_dict:
        ship_matrix_size = len(self.floating_ship.matrix)
        offset = ship_matrix_size // 2
        for col in range(ship_matrix_size):
            for row in range(ship_matrix_size):
                if self.floating_ship.matrix[row][col]:
                    coord = self.cursor_cell_coord[0] - offset + col, self.cursor_cell_coord[1] - offset + row
                    if 0 <= coord[0] < self.col and 0 <= coord[1] < self.row:
                        if not self.cells_dict[coord].ship:
                            self.cells_dict[coord].ship_piece_name = f"{self.floating_ship.matrix[row][col]}_{'h' if self.floating_ship.is_horizontal else 'v'}"
                            self.floating_ship_positions.append(coord)

    def place_ship(self):
        for pos in self.floating_ship_positions:
            self.cells_dict[pos].ship = self.floating_ship
        self.floating_ship = None
        self.floating_ship_positions.clear()

    def get_cell_coord(self, mouse_pos):
        return int((mouse_pos[0] - self.x) // self.cell_size), int((mouse_pos[1] - self.y) // self.cell_size)

    def draw(self, SCREEN):
        for cell_coord, cell in self.cells_dict.items():
            col, row = cell_coord
            coord = (self.x + col * self.cell_size, self.y + row * self.cell_size)

            if cell.ship_piece_name:
                SCREEN.blit(self.images[cell.ship_piece_name], coord)
            if cell.status:
                SCREEN.blit(self.images[cell.status], coord)

        line_width = 2  # this should be dinamic, based on resolution
        for row in range(self.row + 1):
            first_coord = (self.x, self.y + row * self.cell_size)
            second_coord = (self.x + self.col * self.cell_size, self.y + row * self.cell_size)
            pygame.draw.line(SCREEN, self.grid_color, first_coord, second_coord, width=line_width)

        for col in range(self.col + 1):
            first_coord = (self.x + col * self.cell_size, self.y)
            second_coord = (self.x + col * self.cell_size, self.y + self.row * self.cell_size)
            pygame.draw.line(SCREEN, self.grid_color, first_coord, second_coord, width=line_width)