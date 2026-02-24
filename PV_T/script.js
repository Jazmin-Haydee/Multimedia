function listen() {
  let inputArea = document.getElementById('input-area');
  let outputArea = document.getElementById('output-area');

  var recognition = new webkitSpeechRecognition();
  recognition.lang = "es-ES"; //Se cambia a español
  recognition.start();

  recognition.onresult = function(event) {
    let transcript = event.results[0][0].transcript.toLowerCase();
    inputArea.innerHTML = transcript; // Mostramos lo que escuchó

    if (transcript.includes("hola")) {
      outputArea.innerHTML = "¡Hola, ¿como estas?";
    } 
    // NUEVA FUNCIÓN: Lógica para la hora
    else if (transcript.includes("hora")) {
      window.speechSynthesis.speak(new SpeechSynthesisUtterance("Son las " + horaFormateada));
      let fecha = new Date();
      let hora = fecha.getHours();
      let minutos = fecha.getMinutes();
      
      // para que tenga dos digitos
      let horaFormateada = `${hora}:${minutos < 10 ? '0' + minutos : minutos}`;
      
      outputArea.innerHTML = "Son las " + horaFormateada;
    } 
    else if (transcript.includes("clima") || transcript.includes("tiempo")) {
      window.open("https://www.google.com/search?q=clima+actual");
    } 
    else if (transcript.includes("maestro") || transcript.includes("profesor")) {
      outputArea.innerHTML = "Dígame, Jefe...";
    } 
    else {
      outputArea.innerHTML = "No entiendo qué quieres decir con: " + transcript;
    }
  }
}