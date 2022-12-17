
const quantumSize = 128
class TestProcessor extends AudioWorkletProcessor {
    constructor(options) {
      super()
      this.quantaPerFrame = 12
      this.quantaCount = 0
      this.frame = new Int16Array(quantumSize * this.quantaPerFrame)
    }
  
    process(inputs, outputs, parameters) {
      console.log(inputs)
      console.log(this.frame[0])
      console.log(this.frame[1])
      const offset = quantumSize * this.quantaCount
      inputs[0][0].forEach((sample, idx) => this.frame[offset + idx] = Math.floor(sample * 0x7fff))
      this.quantaCount = this.quantaCount + 1
      console.log(this.frame[0])
      console.log(this.frame[1])
      if (this.quantaCount === this.quantaPerFrame) {
        this.port.postMessage(this.frame)
        this.quantaCount = 0
      }
      return true
    }
  }
  
  registerProcessor("pcmWorker", TestProcessor)