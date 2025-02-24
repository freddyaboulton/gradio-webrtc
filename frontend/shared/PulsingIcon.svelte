<script lang="ts">
  import { onDestroy } from "svelte";
  import type { ComponentType } from "svelte";

  export let stream_state: "open" | "closed" | "waiting" = "closed";
  export let audio_source_callback: () => MediaStream;
  export let icon: string | ComponentType = undefined;
  export let icon_button_color: string = "var(--color-accent)";
  export let pulse_color: string = "var(--color-accent)";

  let audioContext: AudioContext;
  let analyser: AnalyserNode;
  let dataArray: Uint8Array;
  let animationId: number;
  let pulseScale = 1;
  let pulseIntensity = 0;

  $: if (stream_state === "open") setupAudioContext();

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
    const source = audioContext.createMediaStreamSource(
      audio_source_callback(),
    );

    source.connect(analyser);

    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.8;
    dataArray = new Uint8Array(analyser.frequencyBinCount);

    updateVisualization();
  }

  function updateVisualization() {
    analyser.getByteFrequencyData(dataArray);

    // Calculate average amplitude for pulse effect
    const average =
      Array.from(dataArray).reduce((a, b) => a + b, 0) / dataArray.length;
    const normalizedAverage = average / 255;
    pulseScale = 1 + normalizedAverage * 0.15;
    pulseIntensity = normalizedAverage;
    animationId = requestAnimationFrame(updateVisualization);
  }

  $: maxPulseScale = 1 + pulseIntensity * 10; // Scale from 1x to 3x based on intensity
</script>

<div class="gradio-webrtc-icon-wrapper">
  <div class="gradio-webrtc-pulsing-icon-container">
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
      class="gradio-webrtc-pulsing-icon"
      style:transform={`scale(${pulseScale})`}
      style:background={icon_button_color}
    >
      {#if typeof icon === "string"}
        <img src={icon} alt="Audio visualization icon" class="icon-image" />
      {:else if icon === undefined}
        <div></div>
      {:else}
        <div>
          <svelte:component this={icon} />
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .gradio-webrtc-icon-wrapper {
    position: relative;
    display: flex;
    max-height: 128px;
    justify-content: center;
    align-items: center;
  }

  .gradio-webrtc-pulsing-icon-container {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .gradio-webrtc-pulsing-icon {
    position: relative;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    transition: transform 0.1s ease;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 2;
  }

  .icon-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: brightness(0) invert(1);
  }

  .pulse-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
    height: 100%;
    border-radius: 50%;
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    opacity: 0.5;
    min-width: 18px;
    min-height: 18px;
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
