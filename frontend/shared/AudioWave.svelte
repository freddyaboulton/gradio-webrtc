<script lang="ts">
  import { onDestroy } from 'svelte';

  export let numBars = 16;
  export let stream_state: "open" | "closed" | "waiting" = "closed";
  export let audio_source_callback: () => MediaStream;
  export let icon: string | undefined = undefined;
  export let icon_button_color: string = "var(--color-accent)";
  export let pulse_color: string = "var(--color-accent)";

  let audioContext: AudioContext;
  let analyser: AnalyserNode;
  let dataArray: Uint8Array;
  let animationId: number;
  let pulseScale = 1;
  let pulseIntensity = 0;

  $: containerWidth = icon 
    ? "128px"
    : `calc((var(--boxSize) + var(--gutter)) * ${numBars})`;

  $: if(stream_state === "open") setupAudioContext();

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
    const source = audioContext.createMediaStreamSource(audio_source_callback());
    
    source.connect(analyser);
    
    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.8;
    dataArray = new Uint8Array(analyser.frequencyBinCount);

    updateVisualization();
  }

  function updateVisualization() {
    analyser.getByteFrequencyData(dataArray);
    
    if (icon) {
      // Calculate average amplitude for pulse effect
      const average = Array.from(dataArray).reduce((a, b) => a + b, 0) / dataArray.length;
      const normalizedAverage = average / 255;
      pulseScale = 1 + (normalizedAverage * 0.15);
      pulseIntensity = normalizedAverage;
    } else {
      // Update bars
      const bars = document.querySelectorAll('.gradio-webrtc-waveContainer .gradio-webrtc-box');
      for (let i = 0; i < bars.length; i++) {
        const barHeight = (dataArray[i] / 255) * 2;
        bars[i].style.transform = `scaleY(${Math.max(0.1, barHeight)})`;
      }
    }

    animationId = requestAnimationFrame(updateVisualization);
  }

  $: maxPulseScale = 1 + (pulseIntensity * 10); // Scale from 1x to 3x based on intensity

</script>

<div class="gradio-webrtc-waveContainer">
{#if icon}
  <div class="gradio-webrtc-icon-container">
    {#if pulseIntensity > 0}
      {#each Array(3) as _, i}
        <div 
          class="pulse-ring"
          style:background={pulse_color}
          style:animation-delay={`${i * 0.4}s`}
          style:--max-scale={maxPulseScale}
          style:opacity={0.5 * pulseIntensity}
        />
      {/each}
    {/if}
    
    <div 
      class="gradio-webrtc-icon" 
      style:transform={`scale(${pulseScale})`}
      style:background={icon_button_color}
    >
      <img 
        src={icon} 
        alt="Audio visualization icon"
        class="icon-image"
      />
    </div>
  </div>
{:else}
  <div class="gradio-webrtc-boxContainer" style:width={containerWidth}>
    {#each Array(numBars) as _}
      <div class="gradio-webrtc-box"></div>
    {/each}
  </div>
{/if}
</div>

<style>
.gradio-webrtc-waveContainer {
  position: relative;
  display: flex;
  min-height: 100px;
  max-height: 128px;
  justify-content: center;
  align-items: center;
}

.gradio-webrtc-boxContainer {
  display: flex;
  justify-content: space-between;
  height: 64px;
  --boxSize: 8px;
  --gutter: 4px;
}

.gradio-webrtc-box {
  height: 100%;
  width: var(--boxSize);
  background: var(--color-accent);
  border-radius: 8px;
  transition: transform 0.05s ease;
}

.gradio-webrtc-icon-container {
  position: relative;
  width: 128px;
  height: 128px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.gradio-webrtc-icon {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  transition: transform 0.1s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2;
}

.icon-image {
  width: 32px;
  height: 32px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  opacity: 0.5;
}

@keyframes pulse {
    0% {
      transform: translate(-50%, -50%) scale(1);
      opacity: 0.5;
    }
    100% {
      transform: translate(-50%, -50%) scale(var(--max-scale, 3));
      opacity: 0;
    }
  }
</style>