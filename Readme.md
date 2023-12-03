# Interactive Video Game Documentation

This document provides a guide on how to create and use nodes in the interactive video game.

## Creating a Node

A node is a fundamental part of the game. It represents a state of the game, which can be a video, a picture, or a choice that the player has to make.

To create a node, you need to add an entry to the `nodes.json` file. Each node is represented as a JSON object with the following attributes:

- `media_path`: The path to the media file for this node. It can be a video or a picture.
- `choices`: A dictionary where the keys are the text of the choices and the values are the names of the nodes that these choices lead to.
- `conditions`: A dictionary where the keys are the text of the choices and the values are lists that define the conditions for these choices.
- `state_actions`: A dictionary that defines the actions to be performed on the game state when this node is reached.
- `is_video`: A boolean value that indicates whether the media file is a video.

Here's an example of a node:

```json
"example_node": {
    "media_path": "assets/example/untitled.jpeg",
    "choices": {"Energy == 5": "test1_node", "Energy > 5": "test2_node", "Mood > 5": "test3_node", "Mood == 5": "test4_node", "Example": "example_node", "Picture": "picture_node", "Home": "home_node"},
    "conditions": {
      "Energy == 5": ["energy", "==", 5],
      "Energy > 5": ["energy", ">", 5],
      "Mood > 5": ["mood", ">", 5],
      "Mood == 5": ["mood", "==", 5]
    },
    "state_actions": {"increase": {"energy": 1}},
    "is_video": false
}
```
## Using Nodes

The game starts with the `intro_node`. From there, the player can make choices that lead to other nodes. The choices are defined in the `choices` attribute of each node.

Each choice can have a condition. The conditions are defined in the `conditions` attribute of each node. A condition is a list with three elements: the name of a state, an operator, and a value. The operator can be `==`, `>`, or `<`. The choice is only available if the condition is true.

When a node is reached, the actions defined in the `state_actions` attribute are performed on the game state. The `state_actions` attribute is a dictionary where the keys are the names of the actions and the values are dictionaries that define the actions. The available actions are `set`, `increase`, and `decrease`.

The `is_video` attribute indicates whether the media file of the node is a video. If it's `true`, the game will play the video. If it's `false`, the game will display the picture.