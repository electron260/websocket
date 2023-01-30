const sampleRate = 44100



function streamaudio(){
  
  let stream
  let audioContext;
  let source;
  let pcmWorker;
  let conn; 


  if (navigator.mediaDevices) {
  console.log("getUserMedia supported.");}
  navigator.mediaDevices.getUserMedia_ = ( navigator.mediaDevices.getUserMedia ||
  navigator.mediaDevices.webkitGetUserMedia ||
  navigator.mediaDevices.mozGetUserMedia ||
  navigator.mediaDevices.msGetUserMedia);


  stream = navigator.mediaDevices.getUserMedia_({
  audio: {
    deviceId: "default",
    sampleRate: sampleRate,
    //sampleSize: 512,
    channelCount: 1
  },
  video: false
}).then( (stream) => {

  console.log(stream) 

  console.log("Stream created")

  audioContext = new window.AudioContext({sampleRate: sampleRate})
  console.log(audioContext)
  source  = audioContext.createMediaStreamSource(stream)
  console.log("source")
  console.log("audio context created")
  



  audioContext.audioWorklet.addModule("static/js/test.js").then( () => {
  console.log(audioContext)
  pcmWorker = new AudioWorkletNode(audioContext, "audio-buffer.worklet" ,{outputChannelCount: [1]})
    source.connect(pcmWorker)
    const mode =  document.getElementById('mode').value;
    if (mode == 'Saving') {
      let username = document.getElementById('username').value;
      conn = new WebSocket("wss://172.21.72.159:8000/wss/save/"+username)}
    else if (mode == 'VoiceCommands') {
      conn = new WebSocket("wss://172.21.72.159:8000/wss/voicecommands")}

    console.log(conn)
    window.audioContext = audioContext;
    window.source = source;
    window.pcmWorker = pcmWorker;
    window.conn = conn;



    pcmWorker.port.onmessage = event => {
      console.log(event.data)
      conn.send(event.data)}
    pcmWorker.port.start()
  })



});  

}








document.getElementById('record').addEventListener('click', function () {
  

  console.log('record');
  streamaudio()  
});

function stopAudioStream(stream) {

  console.log(window.source)
  if (window.source) {
    console.log('disconnecting source')
    source.disconnect();
  }
  console.log(window.pcmWorker)
  if (window.pcmWorker) {
    console.log('disconnecting pcmWorker')
    pcmWorker.port.close();
  }
  console.log(window.conn)
  if (window.conn) {
    console.log('closing connection')
    conn.close();
  }
  
}


  document.getElementById('stop').addEventListener('click', function () {
    console.log('stop');
    stopAudioStream();
  });

  document.getElementById('record').addEventListener('click', function () {
    var mode = document.getElementById('mode').value;
    console.log('record');
    streamaudio()  
  });

