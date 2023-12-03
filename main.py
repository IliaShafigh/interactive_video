import pygame
import pygame_gui
from moviepy.editor import VideoFileClip
import sys
import threading
import json

# nodepath = "node.json"
nodepath = "assets/example/example_nodes.json"
class GameState:
    def __init__(self):
        self.states = {
            'energy': 0,  # Example of a numeric state
            'mood': 0,
            'alcohol': 0
            # Add other states as needed
        }

    def set_state(self, state_name, value):
        self.states[state_name] = value

    def get_state(self, state_name):
        return self.states.get(state_name)

    def increase_state(self, state_name, amount):
        if state_name in self.states:
            self.states[state_name] += amount

    def decrease_state(self, state_name, amount):
        if state_name in self.states:
            self.states[state_name] -= amount

    def check_state(self, state_name, condition):
        return condition(self.get_state(state_name))


class Node:
    def __init__(self, media_path, choices, conditions=None, is_video=True, state_actions=None):
        self.media_path = media_path
        self.choices = choices
        self.conditions = conditions if conditions else {}
        self.is_video = is_video
        # state_actions is a dict with keys 'set', 'increase', 'decrease', each having a dict of state_name: value
        self.state_actions = state_actions if state_actions else {'set': {}, 'increase': {}, 'decrease': {}}




class Game:
    def __init__(self):
        self.game_state = GameState()
        pygame.init()
        pygame.display.set_caption('A Day in the Life of a Developer')

        self.screen_width, self.screen_height = (1280, 720)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height))

        self.game_is_running = True
        self.clock = pygame.time.Clock()
        self.node_history = []
        self.last_frame = None

        self.nodes = self.load_nodes_from_json(nodepath)

        self.current_node = self.nodes['intro_node']
        self.intro_node = self.nodes['intro_node']  # Define intro_node here

        self.video_played = False

    def load_nodes_from_json(self, json_file):
        with open(json_file, 'r') as file:
            data = json.load(file)

        nodes = {}
        for key, value in data.items():
            nodes[key] = Node(**value)

        return nodes

    def run(self):
        while self.game_is_running:
            # set energy level
            time_delta = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_is_running = False

                if event.type == pygame.VIDEORESIZE:
                    # Resize event: Update screen and UI manager resolution
                    self.screen_width, self.screen_height = event.size
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                    self.ui_manager.set_window_resolution((self.screen_width, self.screen_height))

                    # Clear existing UI and show choices if the video has been played
                    if self.video_played:
                        self.ui_manager.clear_and_reset()
                        self.show_choices(self.current_node.choices)

                    # Handle other events
                self.ui_manager.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element.text == 'Replay':
                        self.replay_current_video()
                    elif event.ui_element.text == 'Back' and self.node_history:
                        self.go_back_to_previous_node()
                        continue  # Add this line to skip the rest
                    else:
                        button_text = event.ui_element.text
                        if button_text in self.current_node.choices:
                            self.set_game_state(self.current_node.choices[button_text])

            self.ui_manager.update(time_delta)

            if not self.video_played and self.current_node.media_path:
                self.display_media(self.current_node.media_path, self.current_node.is_video)
            elif self.video_played and self.last_frame and self.current_node.is_video:
                resized_last_frame = pygame.transform.scale(self.last_frame, (self.screen_width, self.screen_height))
                self.screen.blit(resized_last_frame, (0, 0))
                self.ui_manager.draw_ui(self.screen)
                pygame.display.update()

            self.ui_manager.draw_ui(self.screen)
            pygame.display.update()

        pygame.quit()
        sys.exit()

    def set_game_state(self, new_node_key, going_back=False):
        # Store the current node key to history before changing it
        if self.current_node != self.intro_node and not going_back:
            for key, node in self.nodes.items():
                if node == self.current_node:
                    self.node_history.append(key)
                    break
        # Neue Logik für GameState-Änderungen
        node = self.nodes[new_node_key]

        # Überprüfen und Anwenden der 'set' Aktionen
        if 'set' in node.state_actions:
            for state_name, value in node.state_actions['set'].items():
                self.game_state.set_state(state_name, value)

        # Überprüfen und Anwenden der 'increase' Aktionen
        if 'increase' in node.state_actions:
            for state_name, value in node.state_actions['increase'].items():
                self.game_state.increase_state(state_name, value)

        # Überprüfen und Anwenden der 'decrease' Aktionen
        if 'decrease' in node.state_actions:
            for state_name, value in node.state_actions['decrease'].items():
                self.game_state.decrease_state(state_name, value)

        self.current_node = self.nodes[new_node_key]
        self.ui_manager.clear_and_reset()
        self.video_played = False

        # Remove the automatic redirection for nodes with only one choice
        # if len(self.current_node.choices) == 1 and not going_back:
        #     next_node_key = list(self.current_node.choices.values())[0]
        #     self.set_game_state(next_node_key)
        # else:
        if not self.current_node.is_video:
            # For image nodes, show the choices immediately
            self.show_choices(self.current_node.choices)
        # No further action required, wait for video end

    def show_choices(self, choices):
        button_y = self.screen_height - 100
        button_height = 50
        x_start = 10  # Startposition für Buttons

        for choice_text in choices:
            show_button = True

            if choice_text in self.current_node.conditions:
                condition_params = self.current_node.conditions[choice_text]
                if len(condition_params) == 3:
                    state_name, operator, value = condition_params
                    if operator == '==':
                        condition_func = lambda: self.game_state.get_state(state_name) == value
                    elif operator == '>':
                        condition_func = lambda: self.game_state.get_state(state_name) > value
                    elif operator == '<':
                        condition_func = lambda: self.game_state.get_state(state_name) < value
                    else:
                        raise ValueError(f'Invalid operator: {operator}')
                    show_button = condition_func()

            if show_button:
                button_width = 200
                pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((x_start, button_y), (button_width, button_height)),
                    text=choice_text,
                    manager=self.ui_manager
                )
                x_start += button_width + 10

        # Add "Replay" and "Back" buttons if there are multiple choices
        if len(choices) > 1:
            pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((x_start, button_y), (button_width, button_height)),
                text='Replay',
                manager=self.ui_manager,
                object_id='replay_button'
            )
            x_start += button_width + 20

            if self.node_history:
                pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((x_start, button_y), (button_width, button_height)),
                    text='Back',
                    manager=self.ui_manager,
                    object_id='back_button'
                )

        # Update the UI manager to draw the new buttons
        self.ui_manager.update(0)

    def play_video_clip(self, video_path):
        try:
            clip = VideoFileClip(video_path)

            if clip.audio is not None:
                audio_thread = threading.Thread(target=lambda: clip.audio.preview())
                audio_thread.start()
            else:
                audio_thread = None

            for frame in clip.iter_frames(fps=60, dtype='uint8'):
                screen_size = self.screen.get_size()

                frame_surface = pygame.image.frombuffer(frame.tostring(), frame.shape[1::-1], "RGB")
                frame_surface = pygame.transform.scale(frame_surface, screen_size)
                self.screen.blit(frame_surface, (0, 0))
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        sys.exit()
                    elif event.type == pygame.VIDEORESIZE:
                        self.screen_width, self.screen_height = event.size
                        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                        self.ui_manager.set_window_resolution((self.screen_width, self.screen_height))

                self.clock.tick(60)

            self.last_frame = frame_surface  # Store the last frame as a surface
            clip.close()
            if audio_thread:
                audio_thread.join()
            self.video_played = True
            if len(self.current_node.choices) == 1:
                next_node_key = list(self.current_node.choices.values())[0]
                self.set_game_state(next_node_key)
            elif len(self.current_node.choices) > 0:
                self.show_choices(self.current_node.choices)


        except Exception as e:
            print(f"An error occurred during video playback: {e}")
            sys.exit(1)
        #print all gamestates and their values
        print(self.game_state.states)

    def replay_current_video(self):
        # Play the video again
        self.video_played = False
        self.display_media(self.current_node.media_path, self.current_node.is_video)

    def go_back_to_previous_node(self):
        if self.node_history:
            previous_node_key = self.node_history.pop()  # Pop the last node key from the history
            self.set_game_state(previous_node_key, going_back=True)
            self.video_played = False
            self.play_video_clip(self.current_node.media_path)

    def check_for_special_conditions(self):
        # Check for specific conditions to modify gameplay
        if self.game_state['replay_count'] == 3:  # Example condition
            # Modify choices or trigger special events
            if 'Secret Choice' not in self.current_node.choices:
                self.current_node.choices['Secret Choice'] = 'secret_node'

    def display_media(self, media_path, is_video):
        if is_video:
            self.play_video_clip(media_path)
        else:
            # Logic for displaying a picture
            picture = pygame.image.load(media_path)
            picture = pygame.transform.scale(picture, (self.screen_width, self.screen_height))
            self.screen.blit(picture, (0, 0))
            self.ui_manager.draw_ui(self.screen)
            pygame.display.flip()


if __name__ == '__main__':
    game = Game()
    game.run()
