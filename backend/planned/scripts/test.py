import struct

import pvporcupine
import pyaudio

ACCESS_KEY = "peRaidcVma8bYAHuxjPa5oJ0mp/1+dTpCTcFA31k+cRVRaDHpy4VCQ=="

access_key = ACCESS_KEY  # just use the string directly
keyword_paths = [
    "/home/toddsifleet/github/planned.day.backup/models/hey-leo_en_raspberry-pi_v3_0_0/hey-leo_en_raspberry-pi_v3_0_0.ppn"
]

handle = pvporcupine.create(access_key=access_key, keyword_paths=keyword_paths)

# --- PyAudio setup ---
pa = pyaudio.PyAudio()

audio_stream = pa.open(
    rate=handle.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=handle.frame_length,
    input_device_index=2,
)


def get_next_audio_frame():
    """
    Reads one frame of audio from the input device and returns it as
    a sequence of 16-bit signed integers for Porcupine.
    """
    # Read raw bytes from the microphone
    pcm = audio_stream.read(handle.frame_length, exception_on_overflow=False)
    # Convert bytes to tuple of int16 samples
    return struct.unpack_from("h" * handle.frame_length, pcm)


try:
    while True:
        keyword_index = handle.process(get_next_audio_frame())
        if keyword_index >= 0:
            # detection event logic/callback
            print("Wake word detected! index:", keyword_index)
        else:
            print(".", end="", flush=True)
            # your logic here
except KeyboardInterrupt:
    print("Stopping...")
finally:
    if audio_stream is not None:
        audio_stream.stop_stream()
        audio_stream.close()
    pa.terminate()
    handle.delete()
