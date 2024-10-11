<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
  
    export let numBars = 16;
    export let stream_state: "open" | "closed" = "closed";
    export let audio_source: HTMLAudioElement;
  
    let audioContext: AudioContext;
    let analyser: AnalyserNode;
    let dataArray: Uint8Array;
    let animationId: number;
    let is_muted = false;
  
    $: containerWidth = `calc((var(--boxSize) + var(--gutter)) * ${numBars})`;

    $: if(stream_state === "open") setupAudioContext()
  
    onDestroy(() => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      if (audioContext) {
        audioContext.close();
      }
    });
  
    function setupAudioContext() {
      console.log("set up")
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      console.log("audio_source", audio_source.srcObject);
      const source = audioContext.createMediaStreamSource(audio_source.srcObject);
      source.connect(analyser);
      analyser.connect(audioContext.destination);
  
      analyser.fftSize = 64;
      dataArray = new Uint8Array(analyser.frequencyBinCount);
  
      updateBars();
    }
  
    function updateBars() {
      analyser.getByteFrequencyData(dataArray);
      
      const bars = document.querySelectorAll('.box');
      for (let i = 0; i < bars.length; i++) {
        const barHeight = (dataArray[i] / 255) * 2; // Amplify the effect
        bars[i].style.transform = `scaleY(${Math.max(0.1, barHeight)})`;
      }
  
      animationId = requestAnimationFrame(updateBars);
    }
  
    function toggleMute() {
        if (audio_source && audio_source.srcObject) {
            const audioTracks = (audio_source.srcObject as MediaStream).getAudioTracks();
            audioTracks.forEach(track => {
            track.enabled = !track.enabled;
            });
            is_muted = !audioTracks[0].enabled;
        }
    }   

  </script>
  
  <div class="waveContainer">
    <div class="boxContainer" style:width={containerWidth}>
      {#each Array(numBars) as _}
        <div class="box"></div>
      {/each}
    </div>
    <button class="muteButton" on:click={toggleMute}>
      {is_muted ? '🔈' : '🔊'}
    </button>
  </div>
  
  <style>
    .waveContainer {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
  
    .boxContainer {
      display: flex;
      justify-content: space-between;
      height: 64px;
      --boxSize: 8px;
      --gutter: 4px;
    }
  
    .box {
      height: 100%;
      width: var(--boxSize);
      background: var(--color-accent);
      border-radius: 8px;
      transition: transform 0.05s ease;
    }
  
    .muteButton {
      margin-top: 10px;
      padding: 10px 20px;
      font-size: 24px;
      cursor: pointer;
      background: none;
      border: none;
      border-radius: 5px;
      color: var(--color-accent);
    }
  
    :global(body) {
      display: flex;
      justify-content: center;
      background: black;
      margin: 0;
      padding: 0;
      align-items: center;
      height: 100vh;
      color: white;
      font-family: Arial, sans-serif;
    }
  </style>