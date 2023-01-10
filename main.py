
from threading import Thread
import uvicorn
from fastapi import FastAPI, WebSocket,  Request
from fastapi import WebSocket
import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import scipy.io.wavfile as wavf
import numpy as np
import queue
import torch
import librosa
import whisper
from VoiceCommands.CNN.inference import CNNInference
from VoiceCommands.LSTM.inference import LSTMInference
import time

#Whisper 
device = "cuda" if torch.cuda.is_available() else "cpu"
fp16= False
LANGUAGE = "English"
model = whisper.load_model("base.en", device = device)
global mode 

nbsamplefor1sec = 44100

#sensibility
silence_treshold=0.009
root = os.path.dirname(__file__)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')
templates = Jinja2Templates(directory=os.path.join(root, 'templates'))

#method to save samples for training
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

def VoiceCommands(device : str, q : queue.Queue ):
    print(" device :  ", device)
    WUWinference = LSTMInference(device)
    wuwdata = np.zeros(nbsamplefor1sec, dtype=np.float32)
    count = 0
    while True:

        count+=1
        data = q.get()
     
        if (sum(data)!=0):
           
            wuwdata = np.append(wuwdata,data)
            noiseValue = np.abs(wuwdata).mean()
            

            if noiseValue > silence_treshold:
                print("noiseValue ------> ",noiseValue ,"   Wake Up Word triggered :")
                #wavf.write("audio"+str(count)+".wav", 44100, wuwdata)
                new_trigger = WUWinference.get_prediction(torch.tensor(wuwdata).to(device))

                if new_trigger==1:

                        print('Not activated')

                if new_trigger== 0:
                    SpeechToText(q)
            else :
                print("silence")

            wuwdata = wuwdata[-nbsamplefor1sec:]


def SpeechToText(q : queue.Queue):
    print("Activated ")
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

  
    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:
      
        data = await websocket.receive()
        bytes = data['bytes']

        #float32array = array.array('f', bytes).tolist()
        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        databuffer = np.append(databuffer,float32buffer)
    
        if databuffer.size > nbsamplefor1sec:
            datafor1sec = databuffer[:nbsamplefor1sec]

            q.put(datafor1sec)
            databuffer = databuffer[nbsamplefor1sec:]

@app.websocket("/wss/voicecommands")
async def websocket_endpoint(websocket: WebSocket):
    
    q = queue.Queue()

    await websocket.accept()
    t1 = Thread(target=VoiceCommands, args=(device, q,))

    t1.start()


    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:
        data = await websocket.receive()
        bytes = data['bytes']

        
        #float32array = array.array('f', bytes).tolist()
        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        databuffer = np.append(databuffer,float32buffer)
   
        if databuffer.size > nbsamplefor1sec:

            datafor1sec = databuffer[:nbsamplefor1sec]
            #print("queue size : ",q.qsize())
            q.put(datafor1sec)
            databuffer = databuffer[nbsamplefor1sec:]
       
          


if __name__ == '__main__':

    uvicorn.run('main:app', host='192.168.1.23', reload=True, log_level='info',
                ssl_keyfile=os.path.join(root, 'key.pem'),
                ssl_certfile=os.path.join(root, 'cert.pem'))