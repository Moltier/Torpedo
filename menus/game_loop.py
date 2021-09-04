import pygame
from network import send_object


def game_loop(ui, settings, client_data):
    draw_game(ui, client_data)
    if ui.handle_menu_transition(settings.get_resolution()):
        return
    mouse_pos = pygame.mouse.get_pos()

    # Handle inputs
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ui.mode = "exit"

        if ui.chat_is_active:
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    ui.chat_msg = ui.chat_msg[:-1]
                elif event.key in (pygame.K_KP_ENTER, pygame.K_RETURN):
                    ui.chat_is_active = False
                    if ui.chat_msg:
                        if client_data.connected:
                            send_object(("Chat", ui.chat_msg), client_data.socket)
                        ui.update_msg_objects(ui.chat_msg, ui.my_msg_color, settings.get_resolution())
                        ui.chat_msg_num += 1
                        ui.chat_msg = ""
                    else:
                        continue
                else:
                    ui.chat_msg += event.unicode
                ui.menus["msg box"].objects["new msg box"].update_text(new_text=ui.chat_msg)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                client_data.clear(settings.get_resolution())
                ui.create_ship_buttons(settings.get_resolution(), client_data.matrixes[client_data.my_id].ship_count)
                ui.create_game_info_panel(settings.get_resolution())

                if client_data.socket:
                    send_object(("Exiting", None), client_data.socket)
                    print("Closing connection.")
                    client_data.socket.close()

                ui.next_mode = "main menu"
                ui.start_transition_timer()
                # should bring up a sub menu. Basically the options menu, but inside the game loop.

            elif event.key in (pygame.K_KP_ENTER, pygame.K_RETURN):
                ui.chat_is_active = True

            elif client_data.status == "placing ships":
                if event.key == pygame.K_r:
                    client_data.matrixes[client_data.my_id].floating_ship.rotate()
                    client_data.matrixes[client_data.my_id].update_floating_ship()

        elif event.type == pygame.MOUSEMOTION:
            if client_data.status == "placing ships":
                client_data.matrixes[client_data.my_id].update_cursor_cell_coor(mouse_pos)
                if client_data.matrixes[client_data.my_id].prev_cursor_cell_coord != client_data.matrixes[client_data.my_id].cursor_cell_coord:
                    client_data.matrixes[client_data.my_id].update_floating_ship()
                    client_data.matrixes[client_data.my_id].prev_cursor_cell_coord = client_data.matrixes[client_data.my_id].cursor_cell_coord

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left
                if ui.menus["info panel"].objects["exit"].rect.collidepoint(mouse_pos):
                    ui.menus["info panel"].objects["exit"].click()

                elif client_data.status == "picking ships":
                    for ship_type in client_data.matrixes[client_data.my_id].ship_count.keys():
                        if ui.menus["ships"].objects[ship_type].rect.collidepoint(mouse_pos):
                            ui.menus["ships"].objects[ship_type].click()
                            break

                elif client_data.status == "ships placed":
                    if ui.menus[client_data.status].objects["ready"].rect.collidepoint(mouse_pos):
                        ui.menus[client_data.status].objects["ready"].click()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left
                if ui.menus["chat"].objects["chat box"].rect.collidepoint(mouse_pos):
                    ui.chat_is_active = True

                if client_data.status in ("game on", "exiting"):
                    if ui.menus["info panel"].objects["exit"].rect.collidepoint(mouse_pos):
                        client_data.clear(settings.get_resolution())
                        ui.create_ship_buttons(settings.get_resolution(), client_data.matrixes[client_data.my_id].ship_count)
                        ui.create_game_info_panel(settings.get_resolution())

                        if client_data.socket:
                            send_object(("Exiting", None), client_data.socket)
                            print("Closing connection.")
                            client_data.socket.close()

                        ui.next_mode = "main menu"
                        ui.start_transition_timer()

                    elif client_data.status == "game on":
                        if client_data.active_player_id == client_data.my_id:
                            enemy_matrix = client_data.matrixes[client_data.enemy_id]
                            if enemy_matrix.pos_in_matrix(mouse_pos):
                                cell_coord = enemy_matrix.get_cell_coord(mouse_pos)
                                if not enemy_matrix.cells_dict[cell_coord].status:
                                    client_data.my_turn = False
                                    ui.menus["info panel"].objects["player turn"].update_text("Enemy's turn")
                                    send_object(("Shoot", cell_coord), client_data.socket)

                elif client_data.status in ("picking ships", "placing ships"):
                    if client_data.status == "placing ships":
                        my_matrix = client_data.matrixes[client_data.my_id]
                        if len(my_matrix.floating_ship_positions) == my_matrix.floating_ship.hitpoints \
                                and my_matrix.pos_in_matrix(mouse_pos):
                            my_matrix.update_ships()
                            ui.menus["ships count"].objects[my_matrix.floating_ship.name].update_text(
                                new_text=str(my_matrix.ship_count[my_matrix.floating_ship.name]) + 'x')
                            if my_matrix.ship_count[my_matrix.floating_ship.name] == 0:
                                ui.menus["ships"].objects[my_matrix.floating_ship.name].active = False

                            ship_data = (my_matrix.floating_ship.name,
                                         my_matrix.floating_ship.is_horizontal,
                                         my_matrix.cursor_cell_coord)
                            send_object(("New ship data", ship_data), client_data.socket)

                            client_data.matrixes[client_data.my_id].place_ship()

                            if sum(my_matrix.ship_count.values()) > 0:
                                client_data.status = "picking ships"
                            else:
                                client_data.status = "ships placed"
                            continue

                    for ship_type in client_data.matrixes[client_data.my_id].ship_count.keys():
                        if ui.menus["ships"].objects[ship_type].active \
                                and ui.menus["ships"].objects[ship_type].rect.collidepoint(mouse_pos):
                            client_data.matrixes[client_data.my_id].create_ship(ship_type, client_data.ships)
                            client_data.status = "placing ships"
                            if client_data.matrixes[client_data.my_id].ship_count[ship_type] == 0:
                                ui.menus["ships"].objects[ship_type].active = False
                            break

                elif client_data.status == "ships placed":
                    if ui.menus[client_data.status].objects["ready"].rect.collidepoint(mouse_pos):
                        if ui.menus[client_data.status].objects["ready"].down:
                            ui.menus[client_data.status].objects["ready"].down = False
                            client_data.status = "ready"
                            send_object(("Ready", client_data.status), client_data.socket)

                for obj in ui.menus["ships"].objects.values():
                    obj.release()
                for obj in ui.menus["info panel"].objects.values():
                    obj.release()

            elif event.button == 3:  # Right
                if sum(client_data.matrixes[client_data.my_id].ship_count.values()) > 0:
                    client_data.matrixes[client_data.my_id].clear_floating_ship()
                    client_data.status = "picking ships"
                else:
                    client_data.status = "ships placed"


def draw_game(ui, client_data):
    ui.SCREEN.blit(ui.background_img, (0, 0))
    client_data.matrixes[client_data.my_id].draw(ui.SCREEN)

    if client_data.status in ("game on", "exiting"):
        client_data.matrixes[client_data.enemy_id].draw(ui.SCREEN)
        for text_obj in ui.menus["info panel"].objects.values():
            text_obj.draw(ui.SCREEN)

    elif client_data.status in ("picking ships", "placing ships"):
        for text_obj in ui.menus["ships count"].objects.values():
            text_obj.draw(ui.SCREEN)
        for button in ui.menus["ships"].objects.values():
            button.draw(ui.SCREEN)

    elif client_data.status == "ships placed":
        for button in ui.menus["ships placed"].objects.values():
            button.draw(ui.SCREEN)

    else:  # client_data.status == None
        # draw waiting for the other player
        for text_obj in ui.menus["waiting"].objects.values():
            text_obj.draw(ui.SCREEN)

    for obj in ui.menus["chat"].objects.values():
        obj.draw(ui.SCREEN)
    for obj in ui.menus["msg box"].objects.values():
        obj.draw(ui.SCREEN)
    for chat_obj in ui.chat_msg_dict.values():
        if chat_obj.rect.y > ui.menus["chat"].objects["chat box"].rect.y:
            chat_obj.draw(ui.SCREEN)
