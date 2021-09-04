import sys
import pygame
from settings import Settings
from ui import UI
from menus.main_menu import main_menu
from menus.game_loop import game_loop
from menus.options_menu import options_menu
from menus.display_menu import display_menu
from menus.audio_menu import audio_menu
from menus.control_menu import control_menu
from game_data import GameData

# to do:
#   menus helyett group kéne, mert találóbb név
#   connection through internet
#   The ui.create_objects method uses add_objects from menus. add_objects should have a global parameter too.
#       That way i could group them. However, i might want to turn a button off/hide...
#   in game_loop, ESC should bring up a sub menu, where options could be accessed.
#       this could be done by using the options objects, without the background

# known bugs:
#   Menu:
#       Dropdown menu font size wont change.
#       Audio starts from default.

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption("Torpedo")
    settings = Settings()
    ui = UI(settings)
    client_data = GameData(settings.get_resolution())

    ui.create_objects(settings, client_data.matrixes[client_data.my_id].ship_count)
    ui.start_mode("main menu", settings.get_resolution())

    clock = pygame.time.Clock()
    ui.start_transition_timer()

    while True:
        pygame.display.update()
        clock.tick(int(settings.framerate))

        ui.SCREEN.fill((20, 20, 20))

        if ui.mode == "game":
            game_loop(ui, settings, client_data)
        elif ui.mode == "main menu":
            main_menu(ui, settings, client_data)
        elif ui.mode == "options":
            options_menu(ui, settings)
        elif ui.mode == "display":
            display_menu(ui, settings, client_data)
        elif ui.mode == "audio":
            audio_menu(ui, settings)
        elif ui.mode == "controls":
            control_menu(ui, settings)
        elif ui.mode == "other":
            control_menu(ui, settings)  # placeholder
        elif ui.mode == "exit":
            pygame.quit()
            sys.exit()
        else:
            print(f"Unknown ui.mode: {ui.mode}")
