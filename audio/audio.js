// Crear el contexto de audio 
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

// Crear el oscilador
const oscillator = audioContext.createOscillator();
oscillator.type = 'sawtooth'; 
oscillator.frequency.value = 120; 

// Crear el nodo de ganancia (controlar el volumen)
const gainNode = audioContext.createGain();
gainNode.gain.value = 0.3; 

// Nodo de ruido blanco 
const bufferSize = 4096;
const noiseNode = audioContext.createScriptProcessor(bufferSize, 1, 1);
noiseNode.onaudioprocess = (e) => {
  const output = e.outputBuffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    output[i] = Math.random() * 2 - 1; 
  }
};

// Filtro pasa bajos para suavizar el ruido
const filter = audioContext.createBiquadFilter();
filter.type = 'lowpass'; 
filter.frequency.value = 2000; 

// Conectar los nodos 
oscillator.connect(gainNode); 
noiseNode.connect(filter); 
filter.connect(gainNode); 
gainNode.connect(audioContext.destination); 

// Función para cambiar la frecuencia del oscilador automáticamente
function changeFrequency() {
  const newFrequency = Math.random() * 300 + 100; 
  oscillator.frequency.setValueAtTime(newFrequency, audioContext.currentTime); 
  console.log(`Nueva frecuencia: ${newFrequency} Hz`); 
}

// Configurar variables para grabación
let mediaRecorder;
let audioChunks = [];
let stopTimeout;

// Función para iniciar la grabación
async function startRecording() {
  try {
    // Crear un stream a partir del nodo de destino de audio
    const audioStream = audioContext.createMediaStreamDestination();
    gainNode.connect(audioStream); // Conectar el nodo final al destino de grabación

    // Configurar el MediaRecorder con el stream de audio
    mediaRecorder = new MediaRecorder(audioStream.stream);

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data); // Almacenar los fragmentos grabados
    };

    mediaRecorder.onstop = async () => {
      // Crear un Blob con el audio grabado
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      audioChunks = []; // Limpiar los fragmentos para la próxima grabación

      // Enviar el archivo de audio a Lambda
      await sendToLambda(audioBlob);
    };

    mediaRecorder.start(5000); // Grabar en bloques de 5 segundos
    console.log("Grabación iniciada");

    // Configurar temporizador para detener después de 30 segundos
    stopTimeout = setTimeout(() => {
      stopRecording();
    }, 30000); // 30 segundos
  } catch (error) {
    console.error("Error al iniciar la grabación:", error);
  }
}

// Función para detener la grabación
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop(); // Detener la grabación
    console.log("Grabación detenida");
  }
  clearTimeout(stopTimeout); // Limpiar el temporizador
}

// Función para enviar audio a Lambda
async function sendToLambda(audioBlob) {
  const lambdaApiUrl = 'http://localhost:4566/restapis/fmu3tmgpbe/prod/_user_request_/items';

  const formData = new FormData();
  formData.append('file', audioBlob, `audio_${Date.now()}.wav`);

  try {
    const response = await fetch(lambdaApiUrl, {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();
    console.log("Respuesta de Lambda:", result.message);
  } catch (error) {
    console.error("Error al enviar audio a Lambda:", error);
  }
}

// Iniciar automáticamente el sonido y la grabación al cargar la página
(async () => {
  try {
    await audioContext.resume();
    oscillator.start();
    console.log("Sonido de maquinaria iniciado.");

    setInterval(changeFrequency, 2000); // Cambiar la frecuencia periódicamente
    startRecording(); // Iniciar grabación de audio
  } catch (error) {
    console.error('Error al iniciar el sonido:', error);
  }
})();