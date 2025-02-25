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

## `aggregate_bytes_to_16bit`
Aggregate bytes to 16-bit audio samples.

This function takes an iterator of chunks and aggregates them into 16-bit audio samples.
It handles incomplete samples and combines them with the next chunk.

Parameters
```
chunks_iterator : Iterator[bytes]
    An iterator of byte chunks to aggregate
```
Returns
```
Iterator[NDArray[np.int16]]
    An iterator of 16-bit audio samples
```
Example
```python
>>> chunks_iterator = [b'\x00\x01', b'\x02\x03', b'\x04\x05']
>>> for chunk in aggregate_bytes_to_16bit(chunks_iterator):
>>>     print(chunk)
```

## `async_aggregate_bytes_to_16bit`

Aggregate bytes to 16-bit audio samples asynchronously.

Parameters
```
chunks_iterator : Iterator[bytes]
    An iterator of byte chunks to aggregate
```
Returns
```
Iterator[NDArray[np.int16]]
    An iterator of 16-bit audio samples
```
Example
```python
>>> chunks_iterator = [b'\x00\x01', b'\x02\x03', b'\x04\x05']
>>> for chunk in async_aggregate_bytes_to_16bit(chunks_iterator):
>>>     print(chunk)
```

## `wait_for_item`

Wait for an item from an asyncio.Queue with a timeout.

Parameters
```
queue : asyncio.Queue
    The queue to wait for an item from
timeout : float
    The timeout in seconds
```
Returns
```
Any
    The item from the queue or None if the timeout is reached
```

Example
```python
>>> queue = asyncio.Queue()
>>> queue.put_nowait(1)
>>> item = await wait_for_item(queue)
>>> print(item)
```