import pygame
import pygame_gui
from moviepy.editor import VideoFileClip
import sys
import threading


class GameState:
    def __init__(self):
        self.states = {
            'replay_count': {},
            'voiceover_played': False
        }

    def increase_replay_count(self, node_key):
        self.states['replay_count'][node_key] = self.states['replay_count'].get(node_key, 0) + 1
        print(self.states['replay_count'])
        print(self.states['voiceover_played'])

    def check_replay_count(self, node_key, count):
        print(self.states['voiceover_played'])
        return self.states['replay_count'].get(node_key, 0) >= count

    def set_voiceover_played(self, played):
        self.states['voiceover_played'] = played
        print(self.states['replay_count'])
        print(self.states['voiceover_played'])

    def is_voiceover_played(self):
        print(self.states['replay_count'])
        print(self.states['voiceover_played'])
        return self.states['voiceover_played']

    def reset_state(self):
        self.states = {key: {} for key in self.states}
        print(self.states['replay_count'])
        print(self.states['voiceover_played'])


class Node:
    def __init__(self, media_path, choices, is_video=True):
        self.media_path = media_path
        self.choices = choices
        self.is_video = is_video  # True for videos, False for pictures


class Game:
    def __init__(self):
        self.game_state = GameState()  # Instantiate GameState
        pygame.init()
        pygame.display.set_caption('Choice-Based Game')

        self.screen_width, self.screen_height = (1280, 720)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height))

        self.game_is_running = True
        self.clock = pygame.time.Clock()
        self.node_history = []
        self.last_frame = None  # Store the last frame of the video

        # Define Nodes
        self.intro_node = Node("assets/videos/1080p60_3sec.mp4", {"Go to Home": "home_node"})
        self.home_node = Node("assets/videos/home.mp4", {'Voiceover': 'voiceover_node', 'Long Video': 'longvideo_node',
                                                         'Picture': 'picture_node', 'Show example': 'example_node', 'Quit': 'quit'})
        self.voiceover_node = Node("assets/videos/voiceover.mp4",
                                   {"Go to Home": "home_node", 'Show example': 'example_node'})
        self.longvideo_node = Node("assets/videos/1080p60_2min.mp4",
                                   {'Voiceover': 'voiceover_node', "Home": 'home_node'})
        self.picture_node = Node("assets/pictures/icon.jpg", {"Home": "home_node", 'Show example': 'example_node'}, is_video=False)
        self.example_node = Node("assets/videos/1080p60_5sec.mp4",
                                 {'test1': 'test1_node', 'test2': 'test2_node', 'test3': 'test3_node',
                                  'test4': 'test4_node', 'test6': 'test6_node', 'test7': 'test7_node',
                                  'Home': 'home_node'})
        # ... add more nodes as needed ...

        self.nodes = {
            'intro_node': self.intro_node,
            'home_node': self.home_node,
            'voiceover_node': self.voiceover_node,
            'longvideo_node': self.longvideo_node,
            'picture_node': self.picture_node, # TODO implement Node which shows a picture only
            'example_node': self.example_node,
            # ... add more node references as needed ...
        }

        self.current_node = self.intro_node
        self.video_played = False  # Track if the current video has been played

    def run(self):
        while self.game_is_running:
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

        self.current_node = self.nodes[new_node_key]
        self.ui_manager.clear_and_reset()
        self.video_played = False

        # Show choices without auto-proceeding if going back
        if new_node_key == 'example_node' and self.game_state.check_replay_count(self.current_node.video_path, 3):
            self.nodes[new_node_key].choices['Secret Choice'] = 'secret_node'

        if new_node_key == 'voiceover_node':
            self.game_state.set_voiceover_played(True)

        if new_node_key == 'example_node' and self.game_state.is_voiceover_played():
            self.nodes[new_node_key].choices['Additional Voiceover'] = 'additional_voiceover_node'

    def show_choices(self, choices):
        screen_width, screen_height = self.screen.get_size()

        num_buttons = len(choices) + 2 if len(choices) > 1 else len(choices)  # Include Replay and Back buttons
        button_width = screen_width // num_buttons - 20
        button_height = 50
        button_y = screen_height - button_height - 10

        x_start = (screen_width - (button_width + 20) * num_buttons) // 2  # Center buttons horizontally

        if len(choices) > 1:
            # Show the choices buttons
            for choice_text in choices:

                pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((x_start, button_y), (button_width, button_height)),
                    text=choice_text,
                    manager=self.ui_manager
                )
                x_start += button_width + 20

            # Add "Replay" and "Back" buttons if there are multiple choices
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
        else:
            next_node_key = list(choices.values())[0]
            self.set_game_state(next_node_key)

    def play_video_clip(self, video_path):
        try:
            clip = VideoFileClip(video_path)
            audio_thread = threading.Thread(target=lambda: clip.audio.preview())
            audio_thread.start()

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
            audio_thread.join()
            self.video_played = True  # Mark video as played
            if len(self.current_node.choices) > 0:
                self.show_choices(self.current_node.choices)
        except Exception as e:
            print(f"An error occurred during video playback: {e}")
            sys.exit(1)

    def replay_current_video(self):
        # Increase replay count for the current node
        self.game_state.increase_replay_count(self.current_node.media_path)

        # Check if replay count has reached the threshold
        if self.game_state.check_replay_count(self.current_node.media_path, 3):
            # Add the secret choice if not already present
            if 'Secret Choice' not in self.current_node.choices:
                self.current_node.choices['Secret Choice'] = 'secret_node'

        # Play the video again
        self.video_played = False
        self.display_media(self.current_node.media_path, self.current_node.is_video)
    def go_back_to_previous_node(self):
        if self.node_history:
            previous_node_key = self.node_history.pop()  # Pop the last node key from the history
            self.set_game_state(previous_node_key, going_back=True)
            self.video_played = False
            self.play_video_clip(self.current_node.m)

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
            pygame.display.flip()

            # Show choices immediately after displaying the picture
            self.show_choices(self.current_node.choices)

if __name__ == '__main__':
    game = Game()
    game.run()
