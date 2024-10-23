export function get_devices(): Promise<MediaDeviceInfo[]> {
	return navigator.mediaDevices.enumerateDevices();
}

export function handle_error(error: string): void {
	throw new Error(error);
}

export function set_local_stream(
	local_stream: MediaStream | null,
	video_source: HTMLVideoElement
): void {
	video_source.srcObject = local_stream;
	video_source.muted = true;
	video_source.play();
}

export async function get_video_stream(
	include_audio: boolean,
	video_source: HTMLVideoElement,
	device_id?: string,
	track_constraints?: MediaTrackConstraints,
): Promise<MediaStream> {
	const fallback_constraints = track_constraints || {
		width: { ideal: 500 },
		height: { ideal: 500 }
	};

	const constraints = {
		video: device_id ? { deviceId: { exact: device_id }, ...fallback_constraints } : fallback_constraints,
		audio: include_audio
	};

	return navigator.mediaDevices
		.getUserMedia(constraints)
		.then((local_stream: MediaStream) => {
			set_local_stream(local_stream, video_source);
			return local_stream;
		});
}

export function set_available_devices(
	devices: MediaDeviceInfo[]
): MediaDeviceInfo[] {
	const cameras = devices.filter(
		(device: MediaDeviceInfo) => device.kind === "videoinput"
	);

	return cameras;
}