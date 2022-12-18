# from fastapi import FastAPI, WebSocket
# from fastapi.responses import HTMLResponse

# app = FastAPI()

# html = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta http-equiv="X-UA-Compatible" content="IE=edge">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Document</title>
    
# </head>
# <body>
#     <script src="./app.js"></script>
    
# </body>
# </html>
# """


# @app.get("/")
# async def get():
#     return HTMLResponse(html)


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         await websocket.send_text(f"Message text was: {data}")

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

root = os.path.dirname(__file__)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(root, 'static')), name='static')

templates = Jinja2Templates(directory=os.path.join(root, 'templates'))


@app.get("/")

async def get(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.websocket("/wss")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    count=0
    while True:
        count +=1
        data = await websocket.receive()
        bytes = data['bytes']
        print(type(bytes))
        print(len(bytes))
        print(type(data))
        # tuple_of_ints = struct.unpack('=3200h', bytes)
        # print(tuple_of_ints)
        array_of_s16s = array.array('h', bytes)
        with wave.open("audio_filebin"+str(count)+".wav", "wb") as file:
            file.setparams([1,2,16000,32000,'NONE','not compressed'])
            file.writeframes(bytes)
      

if __name__ == '__main__':

    uvicorn.run('main:app', host='0.0.0.0', reload=True, log_level='debug',
                ssl_keyfile=os.path.join(root, 'key.pem'),
                ssl_certfile=os.path.join(root, 'cert.pem'))