class NoiseGenerator extends AudioWorkletProcessor {
    process(inputs, outputs) {
      const output = outputs[0];
      for (let channel = 0; channel < output.length; ++channel) {
        const buffer = output[channel];
        for (let i = 0; i < buffer.length; ++i) {
          buffer[i] = Math.random() * 2 - 1; // Generar ruido blanco
        }
      }
      return true;
    }
  }
  
  registerProcessor('noise-generator', NoiseGenerator);
  