<script lang="ts">
	import { Empty } from "@gradio/atoms";
	import {
		BlockLabel,
	} from "@gradio/atoms";
	import { Music } from "@gradio/icons";
	import type { I18nFormatter } from "@gradio/utils";
	import { createEventDispatcher } from "svelte";
    import { onMount } from "svelte";

    import { start, stop } from "./webrtc_utils";
    import AudioWave from "./AudioWave.svelte";


    export let value: string | null = null;
    export let label: string | undefined = undefined;
    export let show_label = true;
    export let rtc_configuration: Object | null = null;
    export let i18n: I18nFormatter;
    
    export let server: {
        offer: (body: any) => Promise<any>;
    };

    let stream_state: "open" | "closed" | "waiting" = "closed";
    let audio_player: HTMLAudioElement;
    let pc: RTCPeerConnection;
    let _webrtc_id = Math.random().toString(36).substring(2);


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

    async function start_stream(value: string): Promise<string> {
        if( value === "start_webrtc_stream") {
            stream_state = "waiting";
            _webrtc_id = Math.random().toString(36).substring(2)
            value = _webrtc_id;
            console.log("set value to ", value);
            pc = new RTCPeerConnection(rtc_configuration);
            pc.addEventListener("connectionstatechange",
                async (event) => {
                    switch(pc.connectionState) {
                        case "connected":
                            console.info("connected");
                            stream_state = "open";
                            break;
                        case "disconnected":
                            console.info("closed");
                            stop(pc);
                            break;
                        default:
                            break;
                    }
                }
            )
            let stream = null;
            start(stream, pc, audio_player, server.offer, _webrtc_id, "audio").then((connection) => {
                    pc = connection;
                }).catch(() => {
                    console.info("catching")
                    dispatch("error", "Too many concurrent users. Come back later!");
                });
        }
        return value;
    }

    $: start_stream(value).then((val) => {
        value = val;
    });


    
</script>

<BlockLabel
	{show_label}
	Icon={Music}
	float={false}
	label={label || i18n("audio.audio")}
/>
<audio
    class="standard-player"
    class:hidden={value === "__webrtc_value__"}
    on:load
    bind:this={audio_player}
    on:ended={() => dispatch("stop")}
    on:play={() => dispatch("play")}
/>
{#if value !== "__webrtc_value__"}
    <div class="audio-container">
    <AudioWave audio_source={audio_player} {stream_state}/>
    </div>  
{/if}
{#if value === "__webrtc_value__"}
    <Empty size="small">
        <Music />
    </Empty>
{/if}


<style>
    .audio-container {
		display: flex;
		height: 100%;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}

    .standard-player {
        width: 100%;
    }

    .hidden {
        display: none;
    }
</style>