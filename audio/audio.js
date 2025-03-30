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

// Función para cargar el AudioWorklet para el ruido blanco
async function setupNoiseNode() {
  try {
    if (!audioContext.audioWorklet) {
      console.error("AudioWorklet no es compatible con este navegador.");
      return null;
    }

    // Cargar el procesador de trabajo para ruido blanco
    await audioContext.audioWorklet.addModule('noise-generator.js'); // Archivo externo
    const noiseNode = new AudioWorkletNode(audioContext, 'noise-generator');
    console.log("Nodo de ruido blanco configurado correctamente.");
    return noiseNode;
  } catch (error) {
    console.error("Error al configurar el nodo de ruido blanco:", error);
    return null;
  }
}

// Filtro pasa bajos para suavizar el ruido
const filter = audioContext.createBiquadFilter();
filter.type = 'lowpass';
filter.frequency.value = 2000;

// Conectar los nodos
oscillator.connect(gainNode);
gainNode.connect(filter);
filter.connect(audioContext.destination);

// Función para cambiar la frecuencia del oscilador automáticamente
function changeFrequency() {
  const newFrequency = Math.random() * 300 + 100;
  oscillator.frequency.setValueAtTime(newFrequency, audioContext.currentTime);
  console.log(`Nueva frecuencia: ${newFrequency} Hz`);
}

// Configurar variables para grabación
let recordedFragments = 0; // Contador de fragmentos grabados
const maxFragments = 6; // Número máximo de fragmentos (6 audios de 5 segundos)

// URL de la función Lambda
let lambdaApiUrl; // Será cargada desde config.json

// Función para enviar audio a Lambda
async function sendToLambda(audioBlob) {
  try {
    if (!audioBlob || audioBlob.size === 0) {
      console.error("El fragmento de audio está vacío o no válido. No se enviará a Lambda.");
      return;
    }

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

// Función para limpiar recursos después de cada grabación
function cleanUpResources(mediaRecorder, audioStream) {
  console.log("Limpiando recursos tras grabar un fragmento...");
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  if (audioStream) {
    audioStream.disconnect();
  }
  console.log("Recursos limpiados correctamente.");
}

// Función para iniciar la grabación de un solo fragmento
async function recordFragment() {
  try {
    console.log(`Iniciando grabación del fragmento ${recordedFragments + 1}...`);

    // Crear un nuevo destino de MediaStream
    const audioStream = audioContext.createMediaStreamDestination();
    gainNode.connect(audioStream);

    // Validar compatibilidad del tipo MIME
    const mimeType = "audio/webm; codecs=opus";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      console.error(`El tipo MIME ${mimeType} no es compatible con este navegador.`);
      return;
    }

    // Crear el MediaRecorder
    const mediaRecorder = new MediaRecorder(audioStream.stream, { mimeType });

    mediaRecorder.ondataavailable = async (event) => {
      if (event.data.size > 0) {
        console.log("Fragmento de audio disponible:", event.data.size);

        // Crear el blob y enviarlo a Lambda
        const audioBlob = new Blob([event.data], { type: "audio/webm" });
        await sendToLambda(audioBlob);

        console.log(`Fragmento ${recordedFragments + 1} enviado correctamente.`);
      } else {
        console.warn("Se recibió un fragmento vacío, ignorado.");
      }
    };

    mediaRecorder.onstop = () => {
      console.log(`Grabación del fragmento ${recordedFragments + 1} finalizada.`);
      recordedFragments++;

      // Detener completamente después de 6 fragmentos
      if (recordedFragments < maxFragments) {
        setTimeout(() => {
          cleanUpResources(mediaRecorder, audioStream);
          recordFragment(); // Continuar con la siguiente grabación
        }, 500); // Dar tiempo para limpiar antes de iniciar el siguiente fragmento
      } else {
        console.log("Grabación completa de 30 segundos. Se detiene todo.");
        cleanUpResources(mediaRecorder, audioStream);
      }
    };

    mediaRecorder.start(); // Iniciar grabación del fragmento
    console.log("Grabación iniciada para un fragmento de 5 segundos.");

    setTimeout(() => {
      mediaRecorder.stop(); // Detener la grabación tras 5 segundos
    }, 5000);
  } catch (error) {
    console.error("Error al grabar el fragmento:", error);
  }
}

// Función para cargar configuración dinámica
async function fetchConfig() {
  const response = await fetch('config.json');
  if (!response.ok) {
    throw new Error("No se pudo cargar config.json");
  }
  return response.json();
}

(async () => {
  try {
    const config = await fetchConfig();
    lambdaApiUrl = config.lambdaApiUrl;

    const noiseNode = await setupNoiseNode();
    if (noiseNode) {
      noiseNode.connect(filter); // Conectar el nodo de ruido al filtro
    }

    await audioContext.resume();

    if (!oscillatorStarted) {
      oscillator.start();
      oscillatorStarted = true;
      console.log("Sonido de maquinaria iniciado.");
    }

    setInterval(changeFrequency, 2000); // Cambiar frecuencia cada 2 segundos

    // Iniciar grabación de 6 fragmentos de 5 segundos cada uno
    recordFragment();
  } catch (error) {
    console.error('Error al iniciar el sistema:', error);
  }
})();
