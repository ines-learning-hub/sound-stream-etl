// Crear el contexto de audio para generar y procesar sonidos
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

// Crear un oscilador para generar tonos base
const oscillator = audioContext.createOscillator();
oscillator.type = 'sawtooth'; // Onda de diente de sierra para sonido áspero
oscillator.frequency.value = 120; // Frecuencia inicial del oscilador (120 Hz)

// Crear un nodo de ganancia para controlar el volumen
const gainNode = audioContext.createGain();
gainNode.gain.value = 0.3; // Volumen inicial del sonido

// Nodo de ruido blanco (simula el ruido de una máquina)
const bufferSize = 4096; // Tamaño del búfer para el procesador
const noiseNode = audioContext.createScriptProcessor(bufferSize, 1, 1);
// Genera ruido blanco cada vez que se procesa audio
noiseNode.onaudioprocess = (e) => {
  const output = e.outputBuffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    output[i] = Math.random() * 2 - 1; // Genera valores aleatorios entre -1 y 1
  }
};

// Filtro pasa bajos para suavizar el ruido
const filter = audioContext.createBiquadFilter();
filter.type = 'lowpass'; // Tipo del filtro (pasa bajos)
filter.frequency.value = 2000; // Frecuencia de corte inicial (2000 Hz)

// Conectar nodos entre sí
oscillator.connect(gainNode); // El oscilador pasa por el nodo de ganancia
noiseNode.connect(filter); // El ruido pasa primero por el filtro
filter.connect(gainNode); // El filtro pasa al nodo de ganancia
gainNode.connect(audioContext.destination); // Todo llega al destino (altavoces)

// Función para cambiar la frecuencia del oscilador automáticamente
function changeFrequency() {
  const newFrequency = Math.random() * 300 + 100; // Genera una nueva frecuencia entre 100 y 400 Hz
  oscillator.frequency.setValueAtTime(newFrequency, audioContext.currentTime); // Cambia la frecuencia
  console.log(`Nueva frecuencia: ${newFrequency} Hz`); // Imprime la nueva frecuencia en consola
}

// Agregar un evento al botón para iniciar el sonido
document.getElementById('start-button').addEventListener('click', () => {
  audioContext.resume().then(() => {
    oscillator.start(); // Inicia el oscilador
    console.log("Sonido de maquinaria iniciado.");
    setInterval(changeFrequency, 2000); // Cambia la frecuencia cada 2 segundos
  });
});
