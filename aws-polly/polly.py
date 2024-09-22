import boto3
import json
import os
from pygame import mixer

#need to pip install pygame

polly_client = boto3.client('polly')

LANGAUGE_TO_VOICE = {

    'en': 'Matthew',
    'es': 'Miguel',
    'zh': 'Zhiyu',

}

def text_to_speech(text, output_filename, language):

    voice_id = LANGAUGE_TO_VOICE.get((), "Matthew")

    response = polly_client.synthesize_speech(

        Text=text,
        OutputFormat='mp3',
        VoiceId=voice_id
    )

    with open(output_filename, 'wb') as file:
        file.write(response['AudioStream'].read())

    mixer.init()
    mixer.music.load(output_filename)
    mixer.music.play()

    while mixer.music.get_busy():
        continue

def narrate():
    
    language = data.get('selectedLanguage', 'en') 

    file_path = 'example idk where its at'
    with open(file_path, 'r') as file:
        text = file.read()

    output_audio_file = 'output.mp3'  
    text_to_speech(text, output_audio_file, language) 
