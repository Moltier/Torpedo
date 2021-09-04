import pygame
import time
import ctypes
from menu import Menu
from Audio import sound_lib
from object import Button


class UI:
    text_color = (255, 255, 255)

    def __init__(self, settings):
        self.SCREEN = None
        self.mode = None
        self.next_mode = None
        self.game_is_running = False
        self.smooth_transition = True
        self.transition_base_time = 0.15
        self.transition_start_time = None
        self.alpha = 255  # (0-255)

        self.black_image = None
        self.background_img = None
        self.background_img_name = None
        self.prev_background_img_name = None

        self.menus = {}
        self.chat_is_active = False
        self.chat_msg = ""
        self.chat_msg_num = 0  # this might be unnecessary
        self.chat_msg_dict = {}
        self.chat_font_size = None
        self.chat_font_multiplier = None
        self.my_msg_color = (0,255,0)
        self.enemy_msg_color = (255, 0, 0)

        # Other data
        # resolution = settings.get_resolution()
        self.color = (0, 100, 0)
        self.border_color = (40, 40, 40)
        self.text_color = (255, 255, 255)

        self.width_div = 6
        self.height_div = 20
        self.w_diff_div = 20
        self.h_diff_div = 8
        self.font_size_div = 30
        self.menu_button_width = None
        self.menu_button_height = None
        self.menu_button_w_diff = None
        self.menu_button_h_dist = None
        self.general_font_size = None
        self.general_font_multiplier = None

        # Other
        self.set_screen_mode(settings)

    def set_screen_mode(self, settings):
        resolution = settings.get_resolution()
        vsync = 1 if settings.vertical_sync == "True" else 0  # vertical sync isnt fully implemented in pygame

        if settings.full_screen == "True":
            ctypes.windll.user32.SetProcessDPIAware()  # this fixes a problem if correct aspect ratio is choosen, otherwise messes it up.
            flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        else:
            flags = pygame.HWSURFACE | pygame.DOUBLEBUF

        self.SCREEN = pygame.display.set_mode(resolution, flags, vsync=vsync)
        if self.mode and self.menus[self.mode].background_img_name:
            self.background_img = pygame.transform.scale(
                pygame.image.load(f"Images/{self.menus[self.mode].background_img_name}"), resolution).convert()
        self.black_image = pygame.transform.scale(
            pygame.image.load("Images/black.png"), resolution).convert()

        self.update_buttons(settings)

    def update_buttons(self, settings):
        resolution = settings.get_resolution()
        self.menu_button_width = resolution[0] / self.width_div
        self.menu_button_height = resolution[1] / self.height_div
        self.menu_button_w_diff = self.menu_button_width / self.w_diff_div
        self.menu_button_h_dist = self.menu_button_height / self.h_diff_div
        self.update_font_size(settings)

    def update_font_size(self, settings):
        resolution = settings.get_resolution()
        self.general_font_multiplier = settings.get_font_multiplier("general")
        self.chat_font_multiplier = settings.get_font_multiplier("chat")
        self.general_font_size = int(resolution[1] / self.font_size_div / 100 * self.general_font_multiplier)
        self.chat_font_size = int(resolution[1] / self.font_size_div / 100 * self.chat_font_multiplier)

    def start_mode(self, mode, resolution):
        self.mode = mode
        self.background_img_name = self.menus[self.mode].background_img_name
        self.background_img = pygame.transform.scale(
            pygame.image.load(f"Images/{self.background_img_name}"), resolution).convert()

        if self.menus[self.mode].music_name:
            pygame.mixer.music.load(f"Audio/Music/{self.menus[self.mode].music_name}")
            pygame.mixer.music.set_volume(self.menus[self.mode].music_volume)
            pygame.mixer.music.play()

    def apply_volume(self, music_vol, sound_vol):
        # Musics use global and music specific volume. Sound effects dont.
        pygame.mixer.music.set_volume(self.menus[self.mode].music_volume / 10 * (int(music_vol) - 1))

        for sound_effect in sound_lib.sound_effects.values():
            if sound_effect.volume != int(sound_vol) - 1:
                sound_effect.set_volume(int(sound_vol) - 1)

    def handle_menu_transition(self, resolution):
        if self.next_mode:
            if self.alpha == 0:
                if self.menus[self.mode].music_name != self.menus[self.next_mode].music_name:
                    pygame.mixer.music.fadeout(1000)

            self.increase_alpha(resolution)
            self.SCREEN.blit(self.black_image, (0, 0))

            return True

        elif self.alpha > 0:
            if self.background_img:
                self.decrease_alpha()
                self.SCREEN.blit(self.black_image, (0, 0))

            else:
                # use images for every single object instead of rects and lines.
                # then i can just adjust them by set_alpha
                self.mode = self.next_mode
                self.update_background_img(resolution)
                self.next_mode = None

        return False

    def update_background_img(self, resolution):
        if self.menus[self.next_mode].background_img_name != self.background_img_name:
            self.background_img_name = self.menus[self.next_mode].background_img_name
            self.background_img = pygame.transform.scale(
                pygame.image.load(f"Images/{self.background_img_name}"), resolution).convert()

    def start_transition_timer(self):
        self.transition_start_time = time.time()

    def increase_alpha(self, resolution):
        timer = time.time() - self.transition_start_time
        percent = min(int(100 / self.transition_base_time * timer), 100)
        self.alpha = round(255 / 100 * percent)
        self.black_image.set_alpha(self.alpha)
        if self.alpha == 255:
            if self.menus[self.mode].music_name:
                if self.menus[self.mode].music_name != self.menus[self.next_mode].music_name:
                    pygame.mixer.music.load(f"Audio/Music/{self.menus[self.next_mode].music_name}")
                    pygame.mixer.music.set_volume(self.menus[self.next_mode].music_volume)
                    pygame.mixer.music.play()
            else:
                pygame.mixer.music.fadeout(1000)

            self.mode = self.next_mode
            self.update_background_img(resolution)
            self.next_mode = None
            self.transition_start_time = time.time()


    def decrease_alpha(self):
        timer = time.time() - self.transition_start_time
        percent = 100 - max(int(100 / self.transition_base_time * timer), 0)
        self.alpha = int(255 / 100 * percent)
        self.black_image.set_alpha(self.alpha)

    def get_options_data(self):
        if self.mode == "display":
            return [
                ["Full screen", self.menus["display menu buttons"].objects["full screen"].text],
                ["Resolution", self.menus["display menu buttons"].objects["resolution"].text],
                ["Vertical sync", self.menus["display menu buttons"].objects["vertical sync"].text],
                ["Framerate", self.menus["display menu buttons"].objects["framerate"].text],
                ["General text size", self.menus["display menu buttons"].objects["general text size"].text],
                ["Chat text size", self.menus["display menu buttons"].objects["chat text size"].text]
            ]
        elif self.mode == "audio":
            return [
                ["Music volume", str(self.menus["audio menu bars"].objects["music"].level)],
                ["Sound volume", str(self.menus["audio menu bars"].objects["sound"].level)]
            ]
        else:
            print("Unknown ui.mode!")

    def update_msg_objects(self, message, color, resolution):
        w = resolution[0] // 5
        h = resolution[1] // 20
        center_x = resolution[0] // 20 + w / 2
        center_y = resolution[1] - h

        self.chat_msg_dict[self.chat_msg_num] = Button(
            center_x, center_y, w, h, text_color=color,
            text=str(message), font_size=self.chat_font_size, text_positioning="left")

        for i in range(self.chat_msg_num + 1):
            msg_obj = self.chat_msg_dict[i]
            msg_obj.update_pos(y=msg_obj.rect.y - h)


    def create_objects(self, settings, ship_count):
        resolution = settings.get_resolution()

        self.create_main_menu(resolution)
        self.create_options_menu(resolution)
        self.create_general_options_buttons(resolution)
        self.create_display_menu(settings)
        self.create_audio_menu(settings)
        self.create_game_menu()
        self.create_chat(resolution)
        self.create_ship_buttons(resolution, ship_count)
        self.create_other_game_buttons(resolution)
        self.create_game_objects(resolution)
        self.create_game_info_panel(resolution)
        self.create_control_menu(resolution)
        self.create_placeholder_menu(resolution)

    def create_main_menu(self, resolution):
        x = resolution[0] // 2
        y = resolution[1] // 2

        self.menus["main menu"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            background_img_name="galaxy.png", music_name="Imperium Galactica 1.ogg", music_volume=0.1, font_size=self.general_font_size)
        self.menus["main menu"].add_objects(parameters=(
            {
                "name": "new game",
                "type": "button",
                "string": "New Game",
                "image name": None,
                "image alpha": None
            }, {
                "name": "options",
                "type": "button",
                "string": "Options",
                "image name": None,
                "image alpha": None
            }, {
                "name": "exit",
                "type": "button",
                "string": "Exit",
                "image name": None,
                "image alpha": None
            }))

    def create_options_menu(self, resolution):
        x = resolution[0] // 2
        y = resolution[1] // 2

        self.menus["options"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            background_img_name="ocean.png", music_name="Imperium Galactica 2.ogg", music_volume=0.1, font_size=self.general_font_size)
        self.menus["options"].add_objects(parameters=(
            {
                "name": "display",
                "type": "button",
                "string": "Display",
                "image name": None,
                "image alpha": None
            }, {
                "name": "audio",
                "type": "button",
                "string": "Audio",
                "image name": None,
                "image alpha": None
            }, {
                "name": "controls",
                "type": "button",
                "string": "Key Bindings",
                "image name": None,
                "image alpha": None
            }, {
                "name": "other",
                "type": "button",
                "string": "Other",
                "image name": None,
                "image alpha": None
            }, {
                "name": "back",
                "type": "button",
                "string": "Back",
                "image name": None,
                "image alpha": None
            }))

    def create_general_options_buttons(self, resolution):
        x = resolution[0] / 2
        y = resolution[1] / 10 * 9

        self.menus["general options"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_w_diff, placement="horizontal",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            font_size=self.general_font_size)
        self.menus["general options"].add_objects(parameters=(
            {
                "name": "save",
                "type": "button",
                "string": "Save",
                "image name": None,
                "image alpha": None
            }, {
                "name": "back",
                "type": "button",
                "string": "Back",
                "image name": None,
                "image alpha": None
            }, {
                "name": "reset",
                "type": "button",
                "string": "Reset",
                "image name": None,
                "image alpha": None
            }, {
                "name": "default",
                "type": "button",
                "string": "Default",
                "image name": None,
                "image alpha": None
            }))

    def create_display_menu(self, settings):
        resolution = settings.get_resolution()
        text_right_pos = 59  # percent of screen width
        x = int(resolution[0] / 100 * text_right_pos) - self.menu_button_width
        y = resolution[1] // 2

        self.menus["display"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            background_img_name="galaxy.png", music_name="Imperium Galactica 2.ogg", music_volume=0.1, font_size=self.general_font_size, text_positioning="right")
        self.menus["display"].add_objects(parameters=(
            {
                "name": "full screen",
                "type": "text",
                "string": "Full screen",
                "image name": None,
                "image alpha": None
            }, {
                "name": "resolution",
                "type": "text",
                "string": "Resolution",
                "image name": None,
                "image alpha": None
            }, {
                "name": "vertical sync",
                "type": "text",
                "string": "Vertical sync",
                "image name": None,
                "image alpha": None
            }, {
                "name": "framerate",
                "type": "text",
                "string": "Framerate",
                "image name": None,
                "image alpha": None
            }, {
                "name": "general text size",
                "type": "text",
                "string": "General text size",
                "image name": None,
                "image alpha": None
            }, {
                "name": "chat text size",
                "type": "text",
                "string": "Chat text size",
                "image name": None,
                "image alpha": None
            }))

        buttons_left_pos = 60  # percent of screen width
        x = int(resolution[0] / 100 * buttons_left_pos)

        self.menus["display menu buttons"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            font_size=self.general_font_size, text_positioning="left", dinamic=True)
        self.menus["display menu buttons"].add_objects(parameters=(
            {
                "name": "full screen",
                "type": "button",
                "string": settings.full_screen,
                "image name": None,
                "image alpha": None
            }, {
                "name": "resolution",
                "type": "dropdown",
                "string": settings.resolution,
                "choices": ["640x360", "1280x720", "1280x800", "1360x768", "1440x900", "1600x900", "1920x1080", "1920x1200", "2560x1440"]
            }, {
                "name": "vertical sync",
                "type": "button",
                "string": settings.vertical_sync,
                "image name": None,
                "image alpha": None
            }, {
                "name": "framerate",
                "type": "dropdown",
                "string": settings.framerate,
                "choices": ["30", "60"]
            }, {
                "name": "general text size",
                "type": "dropdown",
                "string": settings.general_text_size,
                "choices": ["60%", "70%", "80%", "90%", "100%", "110%", "120%"]
            }, {
                "name": "chat text size",
                "type": "dropdown",
                "string": settings.chat_text_size,
                "choices": ["60%", "70%", "80%", "90%", "100%", "110%", "120%"]
            }))

    def create_audio_menu(self, settings):
        resolution = settings.get_resolution()
        text_right_pos = 59  # percent of screen width
        x = int(resolution[0] / 100 * text_right_pos) - self.menu_button_width
        y = resolution[1] // 2

        self.menus["audio"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            background_img_name="galaxy.png", music_name="Imperium Galactica 2.ogg", music_volume=0.1, font_size=self.general_font_size, text_positioning="right")
        self.menus["audio"].add_objects(parameters=(
            {
                "name": "music",
                "type": "text",
                "string": "Music volume",
                "image name": None,
                "image alpha": None
            }, {
                "name": "sound",
                "type": "text",
                "string": "Sound volume",
                "image name": None,
                "image alpha": None
            }))

        buttons_left_pos = 60  # percent of screen width
        x = int(resolution[0] / 100 * buttons_left_pos)

        self.menus["audio menu bars"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, background_color=(50,50,50), grid_color=(0,0,0),
            font_size=self.general_font_size, text_positioning="right", dinamic=True)
        self.menus["audio menu bars"].add_objects(parameters=(
            {
                "name": "music",
                "type": "bar",
                "level": int(settings.music_volume),
                "max level": 10
            }, {
                "name": "sound",
                "type": "bar",
                "level": int(settings.sound_volume),
                "max level": 10
            }))

    def create_game_menu(self):
        self.menus["game"] = Menu(
            0, 0, 0, 0, background_img_name="ocean.png", music_name="Imperium Galactica 2.ogg", music_volume=0.1)

    def create_chat(self, resolution):
        w = resolution[0] // 5
        h = resolution[1] // 20 * 18
        center_x = resolution[0] // 20 + w / 2
        center_y = resolution[1] // 2

        self.menus["chat"] = Menu(center_x, center_y, w, h)
        self.menus["chat"].add_objects(parameters=(
            {
                "name": "chat box",
                "type": "object",
                "image name": "black.png",
                "image alpha": 125
            },))

        h = resolution[1] // 20
        center_y = resolution[1] - h
        self.menus["msg box"] = Menu(
            center_x, center_y, w, h, text_color=self.text_color,
            font_size=self.chat_font_size, text_positioning="left")
        self.menus["msg box"].add_objects(parameters=(
            {
                "name": "new msg box",
                "type": "text",
                "string": "",
                "image name": "black.png",
                "image alpha": 200
            },))


    def create_ship_buttons(self, resolution, ship_count):
        center_x = resolution[0] // 20 * 17
        center_y = resolution[1] // 10 * 7
        self.menus["ships"] = Menu(
            center_x, center_y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            font_size=self.general_font_size, text_positioning="center", dinamic=False)
        self.menus["ships"].add_objects(parameters=(
            {
                "name": "carrier",
                "type": "button",
                "string": "Carrier",
                "image name": None,
                "image alpha": None
            }, {
                "name": "battleship",
                "type": "button",
                "string": "Battleship",
                "image name": None,
                "image alpha": None
            }, {
                "name": "destroyer",
                "type": "button",
                "string": "Destroyer",
                "image name": None,
                "image alpha": None
            }, {
                "name": "submarine",
                "type": "button",
                "string": "Submarine",
                "image name": None,
                "image alpha": None
            }, {
                "name": "patrol boat",
                "type": "button",
                "string": "Patrol boat",
                "image name": None,
                "image alpha": None
            },))

        center_x = resolution[0] // 20 * 14.5
        center_y = resolution[1] // 10 * 7

        self.menus["ships count"] = Menu(
            center_x, center_y, self.menu_button_width / 3, self.menu_button_height, obj_dist=self.menu_button_h_dist,
            placement="vertical", text_color=self.text_color,
            font_size=self.general_font_size, text_positioning="right", dinamic=True)
        self.menus["ships count"].add_objects(parameters=(
            {
                "name": "carrier",
                "type": "text",
                "string": f'{ship_count["carrier"]}x',
                "image name": None,
                "image alpha": None
            }, {
                "name": "battleship",
                "type": "text",
                "string": f'{ship_count["battleship"]}x',
                "image name": None,
                "image alpha": None
            }, {
                "name": "destroyer",
                "type": "text",
                "string": f'{ship_count["destroyer"]}x',
                "image name": None,
                "image alpha": None
            }, {
                "name": "submarine",
                "type": "text",
                "string": f'{ship_count["submarine"]}x',
                "image name": None,
                "image alpha": None
            }, {
                "name": "patrol boat",
                "type": "text",
                "string": f'{ship_count["patrol boat"]}x',
                "image name": None,
                "image alpha": None
            },))

    def create_other_game_buttons(self, resolution):
        center_x = resolution[0] // 20 * 17
        center_y = resolution[1] // 10 * 7

        self.menus["ships placed"] = Menu(
            center_x, center_y, self.menu_button_width, self.menu_button_height, obj_dist=self.menu_button_h_dist,
            placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            font_size=self.general_font_size, text_positioning="center", dinamic=False)
        self.menus["ships placed"].add_objects(parameters=(
            {
                "name": "ready",
                "type": "button",
                "string": "Ready",
                "image name": None,
                "image alpha": None
            },))

    def create_game_objects(self, resolution):
        center_x = resolution[0] // 2
        center_y = resolution[1] // 2
        width = resolution[0] // 4
        height = resolution[1] // 10

        self.menus["waiting"] = Menu(
            center_x, center_y, width, height, obj_dist=self.menu_button_h_dist,
            placement="vertical", color=self.color, border_color=self.border_color, text_color=self.text_color,
            font_size=self.general_font_size, text_positioning="center", dinamic=True)
        self.menus["waiting"].add_objects(parameters=(
            {
                "name": "waiting",
                "type": "button",
                "string": "Waiting for player 2...",
                "image name": None,
                "image alpha": None
            },))

    def create_game_info_panel(self, resolution):
        center_x = resolution[0] // 20 * 17
        center_y = resolution[1] // 10 * 7
        width = resolution[0] // 4
        height = resolution[1] // 10

        self.menus["info panel"] = Menu(
            center_x, center_y, width, height, obj_dist=self.menu_button_h_dist,
            placement="vertical", color=self.color, border_color=self.border_color, text_color=self.text_color,
            font_size=self.general_font_size, text_positioning="center", dinamic=False)
        self.menus["info panel"].add_objects(parameters=(
            {
                "name": "turn result",
                "type": "button",
                "string": "",
                "image name": None,
                "image alpha": None
            }, {
                "name": "player turn",
                "type": "button",
                "string": "Enemy's turn",
                "image name": None,
                "image alpha": None
            }, {
                "name": "exit",
                "type": "button",
                "string": "Exit",
                "image name": None,
                "image alpha": None
            }))

    def create_control_menu(self, resolution):
        x_pos_div = 8
        y_pos_div = 8
        x = resolution[0] - resolution[0] / x_pos_div
        y = resolution[1] - resolution[1] / y_pos_div

        self.menus["controls"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            background_img_name="galaxy.png", music_name="Imperium Galactica 2.ogg", music_volume=0.1, font_size=self.general_font_size)

    def create_placeholder_menu(self, resolution):
        x_pos_div = 8
        y_pos_div = 8
        x = resolution[0] - resolution[0] / x_pos_div
        y = resolution[1] - resolution[1] / y_pos_div

        self.menus["other"] = Menu(
            x, y, self.menu_button_width, self.menu_button_height, placement="vertical",
            color=self.color, border_color=self.border_color, text_color=self.text_color,
            background_img_name="galaxy.png", music_name="Imperium Galactica 2.ogg", music_volume=0.1, font_size=self.general_font_size)
        self.menus["other"].add_objects(parameters=(
            {
                "name": "back",
                "type": "button",
                "string": "Back",
                "image name": None,
                "image alpha": None
            },))

    def reset_borders(self):
        for button in self.menus["display menu buttons"].objects.values():
            if button.dinamic:
                button.modified = False
        for bar in self.menus["audio menu bars"].objects.values():
            if bar.dinamic:
                bar.modified = False

    def update_text_objects(self, settings):
        self.update_display_buttons(settings)
        self.update_other_texts()

    def update_display_buttons(self, settings):
        self.menus["display menu buttons"].objects["full screen"].update_text(new_text=settings.full_screen, new_font_size=self.general_font_size)
        self.menus["display menu buttons"].objects["resolution"].update_text(new_text=settings.resolution, new_font_size=self.general_font_size)
        self.menus["display menu buttons"].objects["vertical sync"].update_text(new_text=settings.vertical_sync, new_font_size=self.general_font_size)
        self.menus["display menu buttons"].objects["framerate"].update_text(new_text=settings.framerate, new_font_size=self.general_font_size)
        self.menus["display menu buttons"].objects["general text size"].update_text(new_text=settings.general_text_size, new_font_size=self.general_font_size)
        self.menus["display menu buttons"].objects["chat text size"].update_text(new_text=settings.chat_text_size, new_font_size=self.general_font_size)

    def update_audio_levels(self, settings):
        self.menus["audio menu bars"].objects["music"].update_level(settings.music_volume)
        self.menus["audio menu bars"].objects["sound"].update_level(settings.sound_volume)

    def update_other_texts(self):
        self.menus["main menu"].objects["new game"].update_text(new_font_size=self.general_font_size)
        self.menus["main menu"].objects["options"].update_text(new_font_size=self.general_font_size)
        self.menus["main menu"].objects["exit"].update_text(new_font_size=self.general_font_size)

        self.menus["options"].objects["display"].update_text(new_font_size=self.general_font_size)
        self.menus["options"].objects["audio"].update_text(new_font_size=self.general_font_size)
        self.menus["options"].objects["controls"].update_text(new_font_size=self.general_font_size)
        self.menus["options"].objects["other"].update_text(new_font_size=self.general_font_size)
        self.menus["options"].objects["back"].update_text(new_font_size=self.general_font_size)

        self.menus["general options"].objects["save"].update_text(new_font_size=self.general_font_size)
        self.menus["general options"].objects["back"].update_text(new_font_size=self.general_font_size)
        self.menus["general options"].objects["reset"].update_text(new_font_size=self.general_font_size)
        self.menus["general options"].objects["default"].update_text(new_font_size=self.general_font_size)

        self.menus["display"].objects["full screen"].update_text(new_font_size=self.general_font_size)
        self.menus["display"].objects["resolution"].update_text(new_font_size=self.general_font_size)
        self.menus["display"].objects["vertical sync"].update_text(new_font_size=self.general_font_size)
        self.menus["display"].objects["framerate"].update_text(new_font_size=self.general_font_size)
        self.menus["display"].objects["general text size"].update_text(new_font_size=self.general_font_size)
        self.menus["display"].objects["chat text size"].update_text(new_font_size=self.general_font_size)

        self.menus["audio"].objects["music"].update_text(new_font_size=self.general_font_size)
        self.menus["audio"].objects["sound"].update_text(new_font_size=self.general_font_size)

        self.menus["other"].objects["back"].update_text(new_font_size=self.general_font_size)

        self.menus["msg box"].objects["new msg box"].update_text(new_font_size=self.chat_font_size)
