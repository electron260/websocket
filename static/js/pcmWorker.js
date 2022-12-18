
const quantumSize = 128
class TestProcessor extends AudioWorkletProcessor {
    constructor(options) {
      super()
      this.quantaPerFrame = 250
      this.quantaCount = 0
      this.frame = new Int16Array(quantumSize * this.quantaPerFrame)
    }
  
    process(inputs, outputs, parameters) {
      const offset = quantumSize * this.quantaCount
      console.log("IN 0  : ", inputs[0])
      console.log("IN 0 0 : ", inputs[0][0])
      inputs[0][0].forEach((sample, idx) => this.frame[offset + idx] = Math.floor(sample * 0x7fff))
      this.quantaCount = this.quantaCount + 1
      console.log("count", this.quantaCount,"     data : ", this.frame)
      if (this.quantaCount === this.quantaPerFrame) {
        this.port.postMessage(this.frame)
        this.quantaCount = 0
        
      }
      return true
    }
  }
  
  registerProcessor("pcmWorker", TestProcessor)