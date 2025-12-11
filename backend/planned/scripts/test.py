import struct
import time
import wave
from datetime import datetime
from pathlib import Path

import pvporcupine
import pyaudio
from planned import settings

# Configuration
SILENCE_THRESHOLD = 500  # Adjust based on your mic/environment (RMS amplitude)
SILENCE_DURATION = 1.0  # Seconds of silence before saving
OUTPUT_DIR = Path("recordings")

keyword_paths = [
    "/home/toddsifleet/github/planned.day.backup/models/hey-leo_en_raspberry-pi_v3_0_0/hey-leo_en_raspberry-pi_v3_0_0.ppn"
]

handle = pvporcupine.create(
    access_key=settings.PVPORCUPINE_ACCESS_KEY,
    keyword_paths=keyword_paths,
)

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
    pcm = audio_stream.read(handle.frame_length, exception_on_overflow=False)
    return struct.unpack_from("h" * handle.frame_length, pcm)


def calculate_rms(samples):
    """Calculate the root mean square (RMS) of audio samples to detect silence."""
    if not samples:
        return 0
    sum_squares = sum(s * s for s in samples)
    return (sum_squares / len(samples)) ** 0.5


def save_audio(frames, sample_rate, output_path):
    """Save recorded frames to a WAV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)

        # Convert list of sample tuples back to bytes
        for frame in frames:
            wf.writeframes(struct.pack("h" * len(frame), *frame))

    print(f"\nSaved recording to: {output_path}")


def record_until_silence():
    """
    Record audio until silence is detected for SILENCE_DURATION seconds.
    Returns the recorded frames.
    """
    print("\nListening... (speak now)")

    recorded_frames = []
    silence_start = None

    while True:
        frame = get_next_audio_frame()
        recorded_frames.append(frame)

        rms = calculate_rms(frame)

        if rms < SILENCE_THRESHOLD:
            # Currently silent
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start >= SILENCE_DURATION:
                print("Silence detected, stopping recording.")
                break
        else:
            # Sound detected, reset silence timer
            silence_start = None
            print("*", end="", flush=True)

    return recorded_frames


try:
    print("Waiting for wake word...")

    while True:
        keyword_index = handle.process(get_next_audio_frame())

        if keyword_index >= 0:
            print("\nWake word detected!")

            # Record until silence
            frames = record_until_silence()

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = OUTPUT_DIR / f"recording_{timestamp}.wav"

            # Save the recording
            save_audio(frames, handle.sample_rate, output_path)

            print("Waiting for wake word...")
        else:
            print(".", end="", flush=True)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    if audio_stream is not None:
        audio_stream.stop_stream()
        audio_stream.close()
    pa.terminate()
    handle.delete()
