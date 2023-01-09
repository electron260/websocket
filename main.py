
from threading import Thread
import logging
import asyncio
import uvicorn
from fastapi import  Cookie, Depends, FastAPI, Query, WebSocket, status, Request
from fastapi import WebSocket
import websockets
import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import struct
import array
import scipy.io.wavfile as wavf
import wave
import numpy as np
import queue
import torch
import librosa
import whisper
from VoiceCommands.CNN.inference import CNNInference
import time

#Whisper 
fp16= False
LANGUAGE = "English"
model = whisper.load_model("base.en")
global mode 

nbsamplefor1sec = 44100
silence_treshold=0#.009
root = os.path.dirname(__file__)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')

templates = Jinja2Templates(directory=os.path.join(root, 'templates'))

count = 0


def save(q : queue.Queue, username : str):
      count = 0
      audio = np.zeros(nbsamplefor1sec, dtype=np.float32)
      while True: 
            # Récupérez les données audio de la file d'attente
            audiorecup = q.get()
            audio = np.append(audio,audiorecup)
            print("queue size : ",q.qsize())
            # Écrivez les données dans le fichier
            noiseValue = np.abs(audio).mean()
            debutnoise = np.abs(audio[:5000]).mean()

            endnoise =  np.abs(audio[-5000:]).mean()
            if noiseValue > silence_treshold :#and debutnoise < silence_treshold and endnoise < silence_treshold:

                wavf.write("sample-"+username+"-"+str(count)+".wav", 44100, audio)
                print("registered : ", count , "    noiseValue : ",noiseValue,"   debutnoise : ",debutnoise,"   endnoise : ",endnoise)
                count += 1
            audio = audio[-nbsamplefor1sec:]

def VoiceCommands(q : queue.Queue ):
    WUWinference = CNNInference()
    wuwdata = np.zeros(nbsamplefor1sec, dtype=np.float32)
    count = 0
    while True:

        count+=1
        data = q.get()
        print(data)
        if (sum(data)!=0):
            print("silence")

            wuwdata = np.append(wuwdata,data)
            noiseValue = np.abs(wuwdata).mean()
            print("noiseValue ------> ",noiseValue)
            if noiseValue > silence_treshold:
                #wavf.write("audio"+str(count)+".wav", 44100, wuwdata)
                new_trigger = WUWinference.get_prediction(torch.tensor(wuwdata))

                if new_trigger==1:

                        print('Wake Up Word triggered -> not activated')

                if new_trigger== 0:
                    SpeechToText(q)
            wuwdata = wuwdata[-nbsamplefor1sec:]


def SpeechToText(q : queue.Queue):
    print("Wake Up Word triggered -> activated ")
    print(" ************ Speech To Text ************\nListening ...")
    counter = 0
    datarecup = np.zeros(nbsamplefor1sec, dtype=np.float32)
    while counter < 5 :
        STTdata = q.get()
        #wavf.write("STTdata-"+str(counter)+".wav", 44100, STTdata)
        datarecup = np.append(datarecup,STTdata)
        #wavf.write("audio-"+str(counter)+".wav", 44100, datarecup)
        print("STT compteur : ",counter)
        counter += 1
    
    start = time.time()
    print("transcribing ...")

    wavf.write("STTsample.wav", 44100, datarecup)
    STTint16 = librosa.resample(datarecup, orig_sr = 44100, target_sr=16000)
    transcription = model.transcribe(STTint16, language="English")

    print("transcription : ",transcription["text"])
    print("process time : ", time.time() - start)
    #STTint16 = librosa.resample(STTdata, orig_sr = 44100, target_sr=16000)
    #start = time.time()
    #result = model.transcribe(STTint16, language=LANGUAGE)
    #print("process time : ", time.time() - start)
    #STTresult = result["text"]
    #print("transcription : ",STTresult)


@app.get("/")

async def get(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.websocket("/wss/save/{username}")
async def websocket_endpoint(websocket: WebSocket):
    
    q = queue.Queue()
    
    await websocket.accept()
    username = websocket.path_params["username"]
    t1 = Thread(target=save, args=(q,username,))




    t1.start()

    counter = 0
    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:
        counter +=1
        data = await websocket.receive()

        bytes = data['bytes']

        
 
        #float32array = array.array('f', bytes).tolist()

        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        #print("float32buffer : ",float32buffer)
        databuffer = np.append(databuffer,float32buffer)
        #print("data : ",databuffer.size)

        if databuffer.size > nbsamplefor1sec:
            datafor1sec = databuffer[:nbsamplefor1sec]

            q.put(datafor1sec)
            databuffer = databuffer[nbsamplefor1sec:]
            print("q size : ",q.qsize())
            #databuffer = databuffer[nbsamplefor1sec:]

            
            #wavf.write("audio"+str(count)+".wav", 44100, datarecup)
            
@app.websocket("/wss/voicecommands")
async def websocket_endpoint(websocket: WebSocket):
    
    q = queue.Queue()
    
    
    await websocket.accept()

    t1 = Thread(target=VoiceCommands, args=(q,))



    t1.start()

    counter = 0
    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:
        counter +=1
        data = await websocket.receive()

        bytes = data['bytes']

        
 
        #float32array = array.array('f', bytes).tolist()

        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        #print("float32buffer : ",float32buffer)
        databuffer = np.append(databuffer,float32buffer)
        #print("data : ",databuffer.size)

    
        if databuffer.size > nbsamplefor1sec:
            datafor1sec = databuffer[:nbsamplefor1sec]

            q.put(datafor1sec)
            databuffer = databuffer[nbsamplefor1sec:]
            print("q size : ",q.qsize())
            #databuffer = databuffer[nbsamplefor1sec:]

            
            #wavf.write("audio"+str(count)+".wav", 44100, datarecup)
            



if __name__ == '__main__':

    uvicorn.run('main:app', host='172.21.72.189', reload=True, log_level='debug',
                ssl_keyfile=os.path.join(root, 'key.pem'),
                ssl_certfile=os.path.join(root, 'cert.pem'))