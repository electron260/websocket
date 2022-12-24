
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
model = whisper.load_model("tiny.en", fp16=False)


nbsamplefor1sec = 44100
silence_treshold=0.009
root = os.path.dirname(__file__)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')

templates = Jinja2Templates(directory=os.path.join(root, 'templates'))

count = 0


def write_to_file(q):
      count = 0
      while True: 
            # Récupérez les données audio de la file d'attente
            datarecup = q.get()
            print("queue size : ",q.qsize())
            # Écrivez les données dans le fichier
            wavf.write("audio"+str(count)+".wav", 44100, datarecup)
            print("registered : ", count)
            count += 1

def VoiceCommands(q : queue.Queue):
    WUWinference = CNNInference()
    wuwdata = np.zeros(nbsamplefor1sec, dtype=np.float32)
    count = 0
    while True:

        count+=1
        data = q.get()
        wuwdata = np.append(wuwdata,data)
        noiseValue = np.abs(wuwdata).mean()
        print("noiseValue ------> ",noiseValue)
        if noiseValue > silence_treshold:
            wavf.write("audio"+str(count)+".wav", 44100, wuwdata)
            new_trigger = WUWinference.get_prediction(torch.tensor(wuwdata))
            if new_trigger==1:

                    print('Wake Up Word triggered -> not activated')

            if new_trigger== 0:
                SpeechToText(q,wuwdata)
                

        print("wuwdata : ",wuwdata.size)


        wuwdata = wuwdata[-nbsamplefor1sec:]


def SpeechToText(q : queue.Queue, firstsample):
    print("Wake Up Word triggered -> activated ")
    print(" ************ Speech To Text ************\nListening ...")
    counter = 0
    datarecup = firstsample
    while counter < 5 :
        STTdata = q.get()
        datarecup = np.append(datarecup,STTdata)

        print("STT compteur : ",counter)
        counter += 1
    
    start = time.time()
    transcription = model.transcribe(datarecup, language="English")

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

@app.websocket("/wss")
async def websocket_endpoint(websocket: WebSocket):
    q = queue.Queue()
    
    await websocket.accept()

    t1 = Thread(target=VoiceCommands, args=(q,))
    t1.start()


    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:

        data = await websocket.receive()

        bytes = data['bytes']
       
        
 
        #float32array = array.array('f', bytes).tolist()

        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        #print("float32buffer : ",float32buffer)
        databuffer = np.append(databuffer,float32buffer)
        #print("data : ",databuffer.size)
        if databuffer.size > nbsamplefor1sec:
            datarecup = databuffer[:nbsamplefor1sec]
            #print("datarecup : ",datarecup)
            q.put(datarecup)
            print("q size : ",q.qsize())
            databuffer = databuffer[nbsamplefor1sec:]
            
            #wavf.write("audio"+str(count)+".wav", 44100, datarecup)
            





if __name__ == '__main__':

    uvicorn.run('main:app', host='192.168.0.60', reload=True, log_level='debug',
                ssl_keyfile=os.path.join(root, 'key.pem'),
                ssl_certfile=os.path.join(root, 'cert.pem'))