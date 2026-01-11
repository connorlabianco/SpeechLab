// AudioWorklet processor for converting audio to int16 and sending to main thread
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.port.onmessage = (event) => {
      if (event.data === 'stop') {
        this.stopProcessing = true;
      }
    };
    this.stopProcessing = false;
  }

  process(inputs, outputs, parameters) {
    if (this.stopProcessing) {
      return false; // Stop processing
    }

    const input = inputs[0];
    if (input && input.length > 0) {
      const inputData = input[0];
      
      if (inputData && inputData.length > 0) {
        // Convert float32 to int16 (linear16)
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send to main thread
        this.port.postMessage({
          type: 'audioData',
          data: int16Data.buffer
        }, [int16Data.buffer]);
      }
    }

    return true; // Keep processing
  }
}

registerProcessor('audio-processor', AudioProcessor);
