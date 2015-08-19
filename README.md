# raspmusicbox Server

The raspmusicbox Server provides a backend to raspmusicbox Client [LINK] and is meant to be run on a Raspberry Pi. The server can, however, be run on any computer which has the proper dependancies installed.

### DEPENDANCIES
- Python 2.7 (Compatibility with older versions unknown)
- Mutagen (Python package)
- VLC*
- Pi-Blaster**

_*: For some reason, Windows DLL loading with the VLC Python bindings doesn't work properly with newer versions of VLC. If you have issues with starting the program, try using an older version of VLC. (Currently running 2.0.0 with no issues.)_

_**: Only required on the Raspberry Pi._

### USAGE

Extract all files into a folder and edit `server.py` in your preferred editor. There are a few flags at the top of the file that can be customized:

- DIR_PLAYLIST: Directory in which your music is located.
- DIR_COLORS: Directory for song specific color cycles.
- DIR_COLORS_RANDOM: Directory for random color cycles.
- ON_PI: Whether the server is to be run on a Pi or not.
- LED_COMMON_ANODE: Whether the LEDs connected to the Pi are common anode or not.
- RGB_PINS: Which pins are used for red, blue, and green in that order.

Once this has been tweaked to your liking, place your music in the correct directory and start up the server. You should be all set to connect with the client at this point. However, if you'd like to take things a step further you can create your own color cycles.

### CREATING COLOR CYCLES

If you'd like to create a cycle for a specific song, create a `.txt` file with the exact name of the corresponding `.mp3` file. (ex. `test.mp3`'s color cycle would be `test.txt`.) If you'd like to create one for a random song, simply create a `.txt` file with a name of your choice in the random cycle directory. The format for a color cycle is as follows:
```
RED,BLUE,GREEN,TIME
RED,BLUE,GREEN,TIME
RED,BLUE,GREEN,TIME
...
```
The red, green, and blue values are on a scale of 0 to 255. The time given will be the time taken to fade **into** that color from the previous one. **Make sure to not include any spaces, stray newlines, or unnecessary characters anywhere, otherwise it'll break stuff.**

### TO-DO
- Clean up code, a lot.
- Figure out why nobody wants to play MP3s in Python