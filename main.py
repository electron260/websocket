
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
nbsamplefor1sec = 44100
root = os.path.dirname(__file__)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')

templates = Jinja2Templates(directory=os.path.join(root, 'templates'))

count = 0


def write_to_file(q):

      while True: 
            # Récupérez les données audio de la file d'attente
            datarecup = queue.get()
            print("queue size : ",q.qsize())
            # Écrivez les données dans le fichier
            wavf.write("audio"+str(count)+".wav", 44100, datarecup)
            print("registered")


@app.get("/")

async def get(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.websocket("/wss")
async def websocket_endpoint(websocket: WebSocket):
    q = queue.Queue()
    
    await websocket.accept()
    count=0

    t1 = Thread(target=write_to_file, args=(q,))
    t1.start()


    databuffer = np.zeros(nbsamplefor1sec, dtype=np.float32) 
    while True:

        data = await websocket.receive()

        bytes = data['bytes']
       
        
 
        #float32array = array.array('f', bytes).tolist()

        float32buffer = np.frombuffer(bytes, dtype=np.float32)
        print("float32buffer : ",float32buffer)
        databuffer = np.append(databuffer,float32buffer)
        print("data : ",databuffer.size)
        if databuffer.size > nbsamplefor1sec:
            datarecup = databuffer[:nbsamplefor1sec]
            print("datarecup : ",datarecup)
            q.put(datarecup)
            print("q : ",q.qsize())
            databuffer = databuffer[nbsamplefor1sec:]
            
            #wavf.write("audio"+str(count)+".wav", 44100, datarecup)
            


async def register(count):

    data = await q.get()
    if data != None:
            print("data : ",data)
            wavf.write("audio"+str(count)+".wav", 44100, data)
            count += 1
            q.task_done()

       


if __name__ == '__main__':

    uvicorn.run('main:app', host='192.168.1.67', reload=True, log_level='debug',
                ssl_keyfile=os.path.join(root, 'key.pem'),
                ssl_certfile=os.path.join(root, 'cert.pem'))