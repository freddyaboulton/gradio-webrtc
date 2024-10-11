<svelte:options accessors={true} />

<script lang="ts">
	import { Block, UploadText } from "@gradio/atoms";
	import Video from "./shared/InteractiveVideo.svelte";
	import { StatusTracker } from "@gradio/statustracker";
	import type { LoadingStatus } from "@gradio/statustracker";
	import StaticVideo from "./shared/StaticVideo.svelte";
	import StaticAudio from "./shared/StaticAudio.svelte";

	export let elem_id = "";
	export let elem_classes: string[] = [];
	export let visible = true;
	export let value: string = "__webrtc_value__";

	export let label: string;
	export let root: string;
	export let show_label: boolean;
	export let loading_status: LoadingStatus;
	export let height: number | undefined;
	export let width: number | undefined;
	export let server: {
		offer: (body: any) => Promise<any>;
	};

	export let container = false;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;
	export let gradio;
	export let rtc_configuration: Object;
	export let time_limit: number | null = null;
	export let modality: "video" | "audio" = "video";
	export let mode: "send-receive" | "receive" = "send-receive";

	let dragging = false;

	$: console.log("value", value);
</script>

{#if mode == "receive" && modality === "video"}
	<Block
		{visible}
		variant={"solid"}
		border_mode={dragging ? "focus" : "base"}
		padding={false}
		{elem_id}
		{elem_classes}
		{height}
		{width}
		{container}
		{scale}
		{min_width}
		allow_overflow={false}
	>
		<StatusTracker
			autoscroll={gradio.autoscroll}
			i18n={gradio.i18n}
			{...loading_status}
			on:clear_status={() => gradio.dispatch("clear_status", loading_status)}
		/>

		<StaticVideo
			bind:value={value}
			{label}
			{show_label}
			{server}
			{rtc_configuration}
			on:tick={() => gradio.dispatch("tick")}
			on:error={({ detail }) => gradio.dispatch("error", detail)}
		/>
	</Block>

{:else if mode == "receive" && modality === "audio"}
	<Block
		variant={"solid"}
		border_mode={dragging ? "focus" : "base"}
		padding={false}
		allow_overflow={false}
		{elem_id}
		{elem_classes}
		{visible}
		{container}
		{scale}
		{min_width}
	>
		<StatusTracker
		autoscroll={gradio.autoscroll}
		i18n={gradio.i18n}
		{...loading_status}
		on:clear_status={() => gradio.dispatch("clear_status", loading_status)}
	/>
		<StaticAudio
			bind:value={value}
			{label}
			{show_label}
			{server}
			{rtc_configuration}
			i18n={gradio.i18n}
			on:tick={() => gradio.dispatch("tick")}
			on:error={({ detail }) => gradio.dispatch("error", detail)}
		/>
	</Block>
{:else if mode === "send-receive" && modality === "video"}
	<Block
	{visible}
	variant={"solid"}
	border_mode={dragging ? "focus" : "base"}
	padding={false}
	{elem_id}
	{elem_classes}
	{height}
	{width}
	{container}
	{scale}
	{min_width}
	allow_overflow={false}
	>
		<StatusTracker
		autoscroll={gradio.autoscroll}
		i18n={gradio.i18n}
		{...loading_status}
		on:clear_status={() => gradio.dispatch("clear_status", loading_status)}
	/>
		<Video
			bind:value={value}
			{label}
			{show_label}
			active_source={"webcam"}
			include_audio={false}
			{server}
			{rtc_configuration}
			{time_limit}
			on:clear={() => gradio.dispatch("clear")}
			on:play={() => gradio.dispatch("play")}
			on:pause={() => gradio.dispatch("pause")}
			on:upload={() => gradio.dispatch("upload")}
			on:stop={() => gradio.dispatch("stop")}
			on:end={() => gradio.dispatch("end")}
			on:start_recording={() => gradio.dispatch("start_recording")}
			on:stop_recording={() => gradio.dispatch("stop_recording")}
			on:tick={() => gradio.dispatch("tick")}
			on:error={({ detail }) => gradio.dispatch("error", detail)}
			i18n={gradio.i18n}
			stream_handler={(...args) => gradio.client.stream(...args)}
		>
			<UploadText i18n={gradio.i18n} type="video" />
		</Video>
	</Block>
{/if}
