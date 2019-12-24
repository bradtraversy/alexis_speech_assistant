import speech_recognition as sr
import webbrowser
import time
import os
import random
import pyttsx3
import bs4 as bs
import urllib.request
from time import ctime

r = sr.Recognizer()

speaker = pyttsx3.init('sapi5')
voices = speaker.getProperty('voices')
speaker.setProperty('voice', voices[1].id)
rate = speaker.getProperty('rate')
speaker.setProperty('rate', 173)


def record_audio(ask=False):
    with sr.Microphone() as source:
        if ask:
            alexis_speak(ask)
        audio = r.listen(source)
        voice_data = ''
        try:
            voice_data = r.recognize_google(audio)
        except sr.UnknownValueError:
            alexis_speak('Sorry, I did not get that')
        except sr.RequestError:
            alexis_speak('Sorry, my speech service is down')
        return voice_data


def alexis_speak(audio_string):
    print('Computer: ' + audio_string)
    speaker.say(audio_string)
    speaker.runAndWait()


def respond(voice_data):
    if 'what is your name' in voice_data:
        alexis_speak('My name is Alexis')
    if 'what time is it' in voice_data:
        alexis_speak(ctime())
    if 'search' in voice_data:
        search = record_audio('What do you want to search for?')
        url = 'https://google.com/search?q=' + search
        webbrowser.get().open(url)
        alexis_speak('Here is what I found for ' + search)
    if 'find location' in voice_data:
        location = record_audio('What is the location?')
        url = 'https://google.nl/maps/place/' + location + '/&amp;'
        webbrowser.get().open(url)
        alexis_speak('Here is the location of ' + location)
    if 'definition'in voice_data:
        definition=record_audio("what do you need the definition of")
        url=urllib.request.urlopen('https://en.wikipedia.org/wiki/'+definition)
        soup=bs.BeautifulSoup(url,'lxml')
        definitions=[]
        for paragraph in soup.find_all('p'):
            definitions.append(str(paragraph.text))
        try:    
            if definitions[1]:
                alexis_speak ('here is what i found '+definitions[1])
            elif definitions[2]:
                alexis_speak ('Here is what i found '+definitions[2])
        except IndexError:
                alexis_speak("im sorry i could not find the definition for "+definition+", please try a web search") 

    if 'exit' in voice_data:
        exit()


time.sleep(1)
alexis_speak('How can I help you?')
while 1:
    voice_data = record_audio()
    respond(voice_data)
