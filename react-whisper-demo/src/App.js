import React from 'react';
import './App.css';
import WhisperTranscription from './components/WhisperTranscription';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>실시간 음성 인식</h1>
        <p>Powered by Groq and FastRTC</p>
      </header>
      <main className="App-main">
        <WhisperTranscription />
      </main>
    </div>
  );
}

export default App; 