const sampleRate = 44100

function streamaudio(){


  if (navigator.mediaDevices) {
  console.log("getUserMedia supported.");}
  navigator.mediaDevices.getUserMedia_ = ( navigator.mediaDevices.getUserMedia ||
  navigator.mediaDevices.webkitGetUserMedia ||
  navigator.mediaDevices.mozGetUserMedia ||
  navigator.mediaDevices.msGetUserMedia);


  const stream = navigator.mediaDevices.getUserMedia_({
  audio: {
    deviceId: "default",
    sampleRate: sampleRate,
    sampleSize: 512,
    channelCount: 1
  },
  video: false
}).then( (stream) => {

  console.log(stream) 

  console.log("Stream created")

  const audioContext = new window.AudioContext({sampleRate: sampleRate})
  console.log(audioContext)
  const source  = audioContext.createMediaStreamSource(stream)
  console.log("source")
  console.log("audio context created")
  



  audioContext.audioWorklet.addModule("static/js/Processor.js").then( () => {
  console.log(audioContext)
  const pcmWorker = new AudioWorkletNode(audioContext, "process" ,{outputChannelCount: [1]})
    source.connect(pcmWorker)

    const conn = new WebSocket("wss://192.168.1.67:8000/wss")
    console.log(conn)
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


