<script lang="ts">
	import { createEventDispatcher } from "svelte";
	import type { FileData, Client } from "@gradio/client";
	import { BlockLabel } from "@gradio/atoms";
	import  Webcam  from "./Webcam.svelte";
	import { Video } from "@gradio/icons";

	import type { I18nFormatter } from "@gradio/utils";

	export let value: string = null;
	export let label: string | undefined = undefined;
	export let show_label = true;
	export let include_audio: boolean;
	export let i18n: I18nFormatter;
	export let active_source: "webcam" | "upload" = "webcam";
	export let handle_reset_value: () => void = () => {};
	export let stream_handler: Client["stream"];
	export let time_limit: number | null = null;
	export let server: {
		offer: (body: any) => Promise<any>;
	};
	export let rtc_configuration: Object;
	export let track_constraints: MediaTrackConstraints = {};

	const dispatch = createEventDispatcher<{
		change: FileData | null;
		clear?: never;
		play?: never;
		pause?: never;
		end?: never;
		drag: boolean;
		error: string;
		upload: FileData;
		start_recording?: never;
		stop_recording?: never;
		tick: never;
	}>();

	let dragging = false;
	$: dispatch("drag", dragging);

	$: console.log("value", value)

</script>

<BlockLabel {show_label} Icon={Video} label={label || "Video"} />
<div data-testid="video" class="video-container">
	<Webcam
		{rtc_configuration}
		{include_audio}
		{time_limit}
		{track_constraints}
		on:error
		on:start_recording
		on:stop_recording
		on:tick
		{i18n}
		stream_every={0.5}
		{server}
		bind:webrtc_id={value}
	/>

	<!-- <SelectSource {sources} bind:active_source /> -->
</div>

<style>
	.video-container {
		display: flex;
		height: 100%;
		flex-direction: column;
		justify-content: center;
		align-items: center;
	}
</style>
