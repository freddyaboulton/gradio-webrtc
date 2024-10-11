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
    export let autoplay: boolean = true;
    
    export let server: {
        offer: (body: any) => Promise<any>;
    };

    let stream_state = "closed";
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

    $: if( value === "start_webrtc_stream") {
        stream_state = "connecting";
		value = _webrtc_id;
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
		start(null, pc, audio_player, server.offer, _webrtc_id, "audio").then((connection) => {
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
<audio
    class="standard-player"
    class:hidden={value === "__webrtc_value__"}
    on:load
    bind:this={audio_player}
    on:ended={() => dispatch("stop")}
    on:play={() => dispatch("play")}
/>
{#if value !== "__webrtc_value__"}
    <AudioWave audio_source={audio_player} {stream_state}/>
{/if}
{#if value === "__webrtc_value__"}
	<Empty size="small">
		<Music />
	</Empty>
{/if}


<style>
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
</style>