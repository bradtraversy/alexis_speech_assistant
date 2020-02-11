# Alexis Speech Assistant

Python app that uses speech recognition and text-to-speech
This app initially used the Google text-to-speech API, but has been updated to use offline text-to-speech with pyttsx3

### Dependencies

```
pip install speechrecognition
pip install pyttsx3
pip install pyaudio
pip install playsound
pip install PyObjC
```
```
pip install PyAudio
```
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
