

class TestProcessor extends AudioWorkletProcessor {
    buffersize = 44100
    _byteswritten = 0
    _buffer = new Float32Array(this.buffersize)

    constructor(options) {
        this.initBuffer()
      }
  
    process(inputs, outputs, parameters) {
        this.append(inputs[0][0])
        return true

   
    }
    append(channeldata) {
        if (!channeldata) return

        for (let i = 0; i < channeldata.length; i++) {
            this._buffer[this._byteswritten ++] = channeldata[i]
        }
    }

    initBuffer() {
        this._byteswritten = 0
    }

    isBufferEmpty() {
        return this._byteswritten === 0
    }

    isBufferFull() {
        return this._byteswritten === this.buffersize
    }

    flush() {
        this.port.postMessage(
            this._byteswritten < this.buffersize
                ? this._buffer.slice(0, this._byteswritten)
                : this._buffer
            )

        }
}
  registerProcessor("process", TestProcessor)
