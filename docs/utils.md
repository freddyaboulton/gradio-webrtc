# Utils

## `audio_to_bytes`

Convert an audio tuple containing sample rate and numpy array data into bytes.
Useful for sending data to external APIs from `ReplyOnPause` handler.

Parameters
```
audio : tuple[int, np.ndarray]
    A tuple containing:
        - sample_rate (int): The audio sample rate in Hz
        - data (np.ndarray): The audio data as a numpy array
```

Returns
```
bytes
    The audio data encoded as bytes, suitable for transmission or storage
```

Example
```python
>>> sample_rate = 44100
>>> audio_data = np.array([0.1, -0.2, 0.3])  # Example audio samples
>>> audio_tuple = (sample_rate, audio_data)
>>> audio_bytes = audio_to_bytes(audio_tuple)
```

## `audio_to_file`

Save an audio tuple containing sample rate and numpy array data to a file.

Parameters
```
audio : tuple[int, np.ndarray]
    A tuple containing:
        - sample_rate (int): The audio sample rate in Hz
        - data (np.ndarray): The audio data as a numpy array
```
Returns
```
str
    The path to the saved audio file
```
Example
```
```python
>>> sample_rate = 44100
>>> audio_data = np.array([0.1, -0.2, 0.3])  # Example audio samples
>>> audio_tuple = (sample_rate, audio_data)
>>> file_path = audio_to_file(audio_tuple)
>>> print(f"Audio saved to: {file_path}")
```