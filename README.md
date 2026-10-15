# What is Thorn Engine?

Thorn Engine is a bare bones game engine. The goal is for other people to modify the engine and create new things for it. Thorn Engine is not an EXE file. All that is provided to you are the following:

 - Camera
 - Main Script
 - Matrix Functions
 - A Base Object
 - Projection

Required stuff:
- Pygame
- Numpy

The files are written in Python and it is recommended to know a lot about Python before modifying this.

# Controls

- `W` / `S`: move forward / backward; `A` / `D`: strafe; `Q` / `E`: move up / down.
- Arrow keys rotate the camera. Hold the right mouse button and move the mouse for mouse-look.
- Scroll the mouse wheel to dolly the camera forward / backward.
- Press `B` to show the object transform panel. `Tab` selects Move, Rotate, or Scale; `X`, `Y`, and `Z` choose an axis; Left / Right adjust the selected axis.
- Press `F11` to toggle fullscreen, `F12` to open the separate Thorn terminal window, and backtick (`) to toggle system stats.

The F12 terminal is implemented in `ThornEngine/terminal.py`. Its command prompt remains in a reserved, visible row below the output area. It accepts shell commands and includes `cd`, `clear`, `ls`, `system.stats`, and `exit` built-ins. `system.stats` reports OS, kernel, CPU, GPU, and memory details. The terminal and system-stat collection support Windows, macOS, and Linux distributions. Install the Python dependencies with `python -m pip install -r requirements.txt`; Python's Tkinter GUI toolkit may need to be installed separately (for Fedora, `sudo dnf install python3-tkinter`). The engine window also displays a system-monitor-style controls panel along its bottom edge.

# Why the hell did you release this shit unfinished?

The goal was to create something like Linux which is a bare bones operating system without a Graphical User Interface.

# Why "Thorn"? 

Thorn is an runic letter that I think is cool

One more thing, Thorn Engine was made in under 2 days; it might be very buggy or hard to work with and needs a lot of ironing out. I will be working hard on Thorn Engine making sure it is perfect for any young developer like myself. And before anyone ask, the official Thorn Engine release will be free. 

Have fun messing around! - Elpida 
