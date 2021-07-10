# Alexis Speech Assistant

Python app that uses speech recognition and text-to-speech
This app initially used the Google text-to-speech API, but has been updated to use offline text-to-speech with pyttsx3

### Setup

- if you don't already have poetry in your machine , install it using:
1. Linux & MacOS: `brew install poetry`
2. Windows: `pip install poetry`

- If brew not already installed, download Homebrew. 

```
poetry install
```

*Note*
**if you have problem in installing pyaudio library follow these steps:**

1. `sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0`
2. `sudo apt-get install ffmpeg libav-tools`
3. `sudo pip install pyaudio`

(If there is a issue in installing PyAudio use .whl file from this link [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio))  

### Voice Commands

You can add other commands, but these are the ones that exist

- What is your name?
- What time is it
- Search
- Find Location
- Exit

### Apple Mac OS X (Homebrew & PyAudio)
Use Homebrew to install the prerequisite portaudio library, then install PyAudio using pip:

`brew install portaudio`
`pip install pyaudio`

Notes:

If not already installed, download Homebrew.
pip will download the PyAudio source and build it for your version of Python.
Homebrew and building PyAudio also require installing the Command Line Tools for Xcode (more information).

https://people.csail.mit.edu/hubert/pyaudio/
