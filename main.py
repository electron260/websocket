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
from VoiceCommands.Fuzzywuzzy.comparaison import Commands 
from VoiceCommands.TTS.pytts import VocalFeedback
import time

#TEST 
# from transformers import WhisperProcessor, WhisperForConditionalGeneration
# processor = WhisperProcessor.from_pretrained("openai/whisper-small.en")
# model1 = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small.en")
# model1.config.forced_decoder_ids = None


Info = {"Listening": False, "Mode": "None"}

#Whisper 
#device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cpu"
fp16= False
LANGUAGE = "English"
model = whisper.load_model("small.en", device = device)

#import GOSAI commands
GOSAIcommands = Commands()
#import Vocal feedbacks
VocalReturn = VocalFeedback()

nbsamplefor1sec = 44100

#sensibility
silence_treshold=0.0
root = os.path.dirname(__file__)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')
#templates = Jinja2Templates(directory=os.path.join(root, 'templates'))

#add the html and css files to the templates folder
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

                #wavf.write("sample-"+username+"-"+str(count)+".wav", 44100, audio)
                print("registered : ", count , "    noiseValue : ",noiseValue,"   debutnoise : ",debutnoise,"   endnoise : ",endnoise)
                count += 1
            audio = audio[-nbsamplefor1sec:]

def VoiceCommands(device : str, q : queue.Queue, autocalibration : str):
    global Info


    print(" device :  ", device)
    WUWinference = LSTMInference(device)
    wuwdata = np.zeros(0, dtype=np.float32)
    #wuwdata = np.zeros(nbsamplefor1sec, dtype=np.float32)
    counter = 0
    while True & Info["Listening"] == False:
        #print("valeur STT avant le get : ",STTRun)
        if Info["Listening"] != True : 
            data = q.get()
            data,tps = data
            #print("echantillon recup pour WUW")

    
        if (sum(data)!=0) and time.time() - tps < 1.5:
            wuwdata = np.append(wuwdata,data)
           
            if wuwdata.size == 88200:
            
               
                noiseValue = np.abs(wuwdata).mean()
              

                if autocalibration==True:
                    silence_treshold = noiseValue + 0.2*noiseValue
                    print("silence_treshold : ",silence_treshold)
                    autocalibration=False

                if noiseValue > silence_treshold:
                    print("noiseValue ------> ",noiseValue ,"   Wake Up Word triggered :")
                    #wavf.write("audio"+str(count)+".wav", 44100, wuwdata)
                    new_trigger, prob = WUWinference.get_prediction(device,torch.tensor(wuwdata).to(device))

                    if new_trigger==1:

                        print('Not activated -------> ',prob, "    Time Delay: ", time.time()-tps)
                        
                    if new_trigger== 0:
                        SpeechToText(q, wuwdata, counter)
                        counter += 1
                        print('Activated -------> ',prob, "    Time Delay: ", time.time()-tps)
                        #wavf.write("audio"+str(count)+".wav", 44100, wuwdata)
                        wuwdata = np.zeros(0, dtype=np.float32)
                else :
                    print("silence    (",noiseValue,")")

            wuwdata = wuwdata[-nbsamplefor1sec:]
            #count += 1

def SpeechToText(q : queue.Queue, wuwdata, counter : int):
    global Info , SendMessage


    print("Activated ")
    print(" ************ Speech To Text ************\nListening ...")
    #print("STTRun True -> False")
    Info["Listening"] = True
    SendMessage = True

    datarecup = wuwdata
    count = 0 
    while count < 3 :
        STTdata,tps = q.get() 
        
        print("echantillon recup pour STT")
        #wavf.write("STTdata-"+str(counter)+".wav", 44100, STTdata)
        datarecup = np.append(datarecup,STTdata)
        #wavf.write("audio-"+str(counter)+".wav", 44100, datarecup)
        print("STT compteur : ",count)
        count += 1

      
    Info["Listening"] = False
    SendMessage = True


    
    print("transcribing ...")


    # wavf.write("STTsample-"+str(counter)+".wav", 44100, datarecup)
    STTint16 = librosa.resample(datarecup, orig_sr = 44100, target_sr=16000)

    # # transcription = model.transcribe(STTint16, language="English")
    # input_features = processor(STTint16, sampling_rate=16000, return_tensors="pt").input_features 
    # #print("input_features : ",input_features)
    # predicted_ids = model1.generate(input_features)
    # #print("predicted_ids : ",predicted_ids)
    # transcription2 = processor.batch_decode(predicted_ids, skip_special_tokens=True)


    startWhisper = time.time()
    transcription = model.transcribe(STTint16, language="English")
    print("Whisper time : ", time.time() - startWhisper)
    GOSAIcommands.comparaison(transcription)
    print("transcription : ",transcription["text"])
    counter +=1
    
    if len(GOSAIcommands.modeactive) != 0 :
        print("Application mode : ",GOSAIcommands.modeactive)
        VocalReturn.speak(GOSAIcommands.modeactive[1], GOSAIcommands.modeactive[0])

        Info["Mode"] = GOSAIcommands.modeactive[1] + " " + GOSAIcommands.modeactive[0]
        SendMessage = True
        
    print("process time : ", time.time() - startWhisper)
    GOSAIcommands.modeactive = []
    #print("STTRun False -> True")

    

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
            print("echantillon envoyé pour queue")
            databuffer = databuffer[nbsamplefor1sec:] 

@app.websocket("/wss/voicecommands")
async def websocket_endpoint(websocket: WebSocket):

    global Info , SendMessage
    SendMessage = True
    autocalibration = True
    q = queue.Queue()

    await websocket.accept()
    t1 = Thread(target=VoiceCommands, args=(device, q, autocalibration,))

    t1.start()



    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:
        if SendMessage == True:
            #send websocket to client to display "listening"
            await websocket.send_json(Info)
            print("message sent to client : ", Info)
            SendMessage = False

        data = await websocket.receive()
        bytes = data['bytes']
        
        #float32array = array.array('f', bytes).tolist()
        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        databuffer = np.append(databuffer,float32buffer)
   
        if databuffer.size > nbsamplefor1sec:

            datafor1sec = databuffer[:nbsamplefor1sec]
            #print("queue size : ",q.qsize())
            q.put((datafor1sec, time.time()))
            #print("echantillon envoyé pour queue")
            databuffer = databuffer[nbsamplefor1sec:]
       
          


if __name__ == '__main__':

    uvicorn.run('main:app', host='192.168.1.51', reload=True, log_level='info',
                ssl_keyfile=os.path.join(root, 'cert/key.pem'),
                ssl_certfile=os.path.join(root, 'cert/cert.pem'))








        