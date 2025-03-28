// Crear el contexto de audio 
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

// Crear el oscilador
const oscillator = audioContext.createOscillator();
oscillator.type = 'sawtooth'; 
oscillator.frequency.value = 120; 

let oscillatorStarted = false;

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
let stopTimeout;

// Función para iniciar la grabación
async function startRecording() {
  try {
    // Crear un stream a partir del nodo de destino de audio
    const audioStream = audioContext.createMediaStreamDestination();
    gainNode.connect(audioStream); // Conectar el nodo final al destino de grabación

    // Configurar el MediaRecorder con el stream de audio
    mediaRecorder = new MediaRecorder(audioStream.stream);

    // Procesar cada fragmento de audio tan pronto como esté disponible
    mediaRecorder.ondataavailable = async (event) => {
      console.log("Fragmento de audio disponible:", event.data);
      const audioBlob = new Blob([event.data], { type: 'audio/webm;codecs=opus' }); // Crear el blob individual
      console.log("Enviando fragmento de audio a Lambda:", audioBlob.size);

      // Enviar el fragmento de audio a Lambda
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

// Función para cargar configuración dinámica
async function fetchConfig() {
  const response = await fetch('config.json'); // Carga el archivo generado
  if (!response.ok) {
    throw new Error("No se pudo cargar config.json");
  }
  return response.json();
}

let lambdaApiUrl;

(async () => {
  try {
      // Cargar configuración desde config.json
      const config = await fetchConfig();
      lambdaApiUrl = config.lambdaApiUrl;

      await audioContext.resume();

      if (!oscillatorStarted) {
        oscillator.start();
        oscillatorStarted = true; // Marcar como iniciado
        console.log("Sonido de maquinaria iniciado.");
      }

      setInterval(changeFrequency, 2000); // Cambiar la frecuencia periódicamente
      startRecording(); // Iniciar grabación de audio
  } catch (error) {
      console.error('Error al cargar configuración o iniciar el sonido:', error);
  }
})();

// Función para enviar audio a Lambda
async function sendToLambda(audioBlob) {
  try {
      console.log("Enviando fragmento a Lambda:", audioBlob.size);
      const response = await fetch(lambdaApiUrl, {
          method: 'POST',
          headers: {
              "Content-Type": "application/octet-stream", // Indicar que se envía un archivo binario
          },
          body: audioBlob, // Enviar directamente el Blob como cuerpo
          mode: 'cors', // Habilitar CORS
      });

      if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
      }

      console.log("Audio enviado exitosamente a Lambda.");
  } catch (error) {
      console.error("Error al enviar audio a Lambda:", error);
  }
}