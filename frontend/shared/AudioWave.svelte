<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
  
    export let numBars = 16;
    export let stream_state: "open" | "closed" | "waiting" = "closed";
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
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(audio_source.srcObject);
      
      // Only connect to analyser, not to destination
      source.connect(analyser);
      
      // Configure analyser
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.8; // Add smoothing to make visualization less jittery
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
</script>
  
<div class="waveContainer">
  <div class="boxContainer" style:width={containerWidth}>
    {#each Array(numBars) as _}
      <div class="box"></div>
    {/each}
  </div>
</div>
  
<style>
  .waveContainer {
    position: relative;
    display: flex;
    min-height: 100px;
    max-height: 128px;
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
</style>