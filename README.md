# SkEye
_Pronounced "Sky"_

CEN4907C Design Project (Formerly known as The Citadel)

## Introduction
SkEye is a tabletop interactive mapping system that uses AR/XR technology to track physical objects placed on a surface and dynamically projects or displays information around them, turning a table into a programmable spatial interface. SkEye allows users to upload their own scenarios, step through them, and replay past actions on the board.

## Architectural Elements
### External Interface
SkEye can output a window to a computer screen showing the camera output, perform a calibration routine, and track an object, outputting the objects coordinates and current location onto the screen. To connect to the persistent state, the current functionality of SkEye's software allows for recording and playback of object tracking sequences.

### Persistent State
SkEye allows users to save and play back replays of previous actions occurring on the tabletop. To record, a user can press `s` and move the object around. When finished, pressing `s` saves the recording, which can be replayed, allowing the user to see the location of tokens during the recorded period of time on the displayed graph. This functionality saves playbacks to a persistent JSON file which can be loaded later to play the recording again.

### Internal Systems

SkEye makes use of the OpenCV library to process images. For example, SkEye uses a script to generate ArUco markers (for corner detection) and detect these markers to determine the bounds of the board. Additionally, SkEye uses numpy and OpenCV modules to normalize the detected board into a coordinate plane, running camera pixels through a matrix to convert from px to coordinates, and an inverse matrix to do the opposite operation.

Currently, we are using the OpenCV Python library, but if problems arise with performance when we scale down to a smaller CPU, we may pivot to using C++ to deal with performance constraints. However, Python was chosen for the time being as it made it easy to quickly stand up multiple features for our proof-of-concept.


## Information Handling
### Communication
We are able to communicate with the webcam via USB and plan to when we switch to using a headless (Raspberry Pi) setup. The different python scripts also output to the terminal / save to files, meaning that other parts of the system will eventually be able to access these streams and use the output for their operations. Furthermore, we are able to communicate with the program using certain keybinds (such as numbers 1-5 for changing color detection, and s to save a recording). This allows us to make the system interactive until we have our physical controller set up.

### Integrity and Resilience
The current calibration setup runs through a set of test cases. If any of these fail during the 60s calibration period without being corrected, the calibration fails and the program exits. These criteria, including camera steadiness, brightness, how close the camera is to the table, etc, all make sure that SkEye can operate under the best conditions. Our goal for the next milestone is to set up calibration that happens continuously, helping to notify users of any issues that may arise during use.

## Software Setup

To set up the software environment for running our code, follow the following steps:
- navigate to the software/ directory
- run `./setup.sh`
  - this will create the .venv/ directory from the dependencies in  `requirements.txt`
- run `source ./venv/bin/activate`

## References
**Pitch Link:** https://youtu.be/Z7oE
## Contributors

#### Hardware
- Sami Al-Jamal
- Anders Swenson

#### Software
- Anna Hudson
- Timothy Macias
- Jacob Oram
