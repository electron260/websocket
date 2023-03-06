# websocket
client sending audio in realtime to the server via websocket 

CLIENT : 
(Javascript/HTML client)  
app.js : using the mediadevices api to record audio from a webpage 
worklet.js :  the audio worklet node attached to the audio stream 

SERVER : 
(Pyhton server)
main.py : using FastAPI, receiving the audio from the web client and using the VoiceCommands repo to process the audio


