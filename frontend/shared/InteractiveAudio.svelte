<script lang="ts">
	import {
		BlockLabel,
	} from "@gradio/atoms";
	import type { I18nFormatter } from "@gradio/utils";
	import { createEventDispatcher } from "svelte";
    import { onMount } from "svelte";
    import { StreamingBar } from "@gradio/statustracker";
    import {
		Circle,
		Square,
		Spinner,
        Music
	} from "@gradio/icons";

    import { start, stop } from "./webrtc_utils";
    import AudioWave from "./AudioWave.svelte";



    export let value: string | null = null;
    export let label: string | undefined = undefined;
    export let show_label = true;
    export let rtc_configuration: Object | null = null;
    export let i18n: I18nFormatter;
    export let time_limit: number | null = null;
    export let track_constraints: MediaTrackConstraints = {};
    let _time_limit: number | null = null;

    $: console.log("time_limit", time_limit);
    
    export let server: {
        offer: (body: any) => Promise<any>;
    };

    let stream_state: "open" | "closed" | "waiting" = "closed";
    let audio_player: HTMLAudioElement;
    let pc: RTCPeerConnection;
    let _webrtc_id = null;


    const dispatch = createEventDispatcher<{
        tick: undefined;
        error: string
        play: undefined;
        stop: undefined;
	}>();


    onMount(() => {
        window.setInterval(() => {
            if (stream_state == "open") {
                dispatch("tick");
            }
        }, 1000);
        }
    )

    async function start_stream(): Promise<void> {
        if( stream_state === "open"){
            stop(pc);
            stream_state = "closed";
            _time_limit = null;
            return;
        }
            _webrtc_id = Math.random().toString(36).substring(2);
            value = _webrtc_id;
            pc = new RTCPeerConnection(rtc_configuration);
            pc.addEventListener("connectionstatechange",
                async (event) => {
                    switch(pc.connectionState) {
                        case "connected":
                            console.info("connected");
                            stream_state = "open";
                            _time_limit = time_limit;
                            break;
                        case "disconnected":
                            console.info("closed");
                            stream_state = "closed";
                            _time_limit = null;
                            stop(pc);
                            break;
                        default:
                            break;
                    }
                }
            )
            stream_state = "waiting"
            let stream = null
            
            try {
			    stream = await navigator.mediaDevices.getUserMedia({ audio: track_constraints });
            } catch (err) {
                if (!navigator.mediaDevices) {
                    dispatch("error", i18n("audio.no_device_support"));
                    return;
                }
                if (err instanceof DOMException && err.name == "NotAllowedError") {
                    dispatch("error", i18n("audio.allow_recording_access"));
                    return;
                }
                throw err;
            }
            if (stream == null) return;

            start(stream, pc, audio_player, server.offer, _webrtc_id, "audio").then((connection) => {
                    pc = connection;
                }).catch(() => {
                    console.info("catching")
                    dispatch("error", "Too many concurrent users. Come back later!");
                });
        }
    

    
</script>

<BlockLabel
	{show_label}
	Icon={Music}
	float={false}
	label={label || i18n("audio.audio")}
/>
<div class="audio-container">
    <audio
        class="standard-player"
        class:hidden={value === "__webrtc_value__"}
        on:load
        bind:this={audio_player}
        on:ended={() => dispatch("stop")}
        on:play={() => dispatch("play")}
    />
    <AudioWave audio_source={audio_player} {stream_state}/>
    <StreamingBar time_limit={_time_limit} />
    <div class="button-wrap">
        <button
            on:click={start_stream}
            aria-label={"start stream"}
        >
            {#if stream_state === "waiting"}
                <div class="icon-with-text" style="width:var(--size-24);">
                    <div class="icon color-primary" title="spinner">
                        <Spinner />
                    </div>
                    {i18n("audio.waiting")}
                </div>
            {:else if stream_state === "open"}
                <div class="icon-with-text">
                    <div class="icon color-primary" title="stop recording">
                        <Square />
                    </div>
                    {i18n("audio.stop")}
                </div>
            {:else}
                <div class="icon-with-text">
                    <div class="icon color-primary" title="start recording">
                        <Circle />
                    </div>
                    {i18n("audio.record")}
                </div>
            {/if}
        </button>
    </div>
</div>

<style>

    .audio-container {
		display: flex;
		height: 100%;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}


    :global(::part(wrapper)) {
        margin-bottom: var(--size-2);
    }

    .standard-player {
        width: 100%;
        padding: var(--size-2);
    }

    .hidden {
        display: none;
    }


	.button-wrap {
        margin-top: var(--size-2);
        margin-bottom: var(--size-2);
		background-color: var(--block-background-fill);
		border: 1px solid var(--border-color-primary);
		border-radius: var(--radius-xl);
		padding: var(--size-1-5);
		display: flex;
		bottom: var(--size-2);
		box-shadow: var(--shadow-drop-lg);
		border-radius: var(--radius-xl);
		line-height: var(--size-3);
		color: var(--button-secondary-text-color);
	}

	.icon-with-text {
		width: var(--size-20);
		align-items: center;
		margin: 0 var(--spacing-xl);
		display: flex;
		justify-content: space-evenly;
	}

	@media (--screen-md) {
		button {
			bottom: var(--size-4);
		}
	}

	@media (--screen-xl) {
		button {
			bottom: var(--size-8);
		}
	}

	.icon {
		width: 18px;
		height: 18px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.color-primary {
		fill: var(--primary-600);
		stroke: var(--primary-600);
		color: var(--primary-600);
	}
</style>