import asyncio
import time

import numpy as np
import pvcheetah
import pvcobra
import pvporcupine
from loguru import logger
from pvrecorder import PvRecorder

from planned import settings

ACCESS_KEY = settings.PVPORCUPINE_ACCESS_KEY

# Configuration
VOICE_THRESHOLD = 0.3  # Cobra voice probability threshold (0.0 to 1.0)
SILENCE_DURATION = 0.5  # Seconds of silence before processing

keyword_paths = [
    "/home/toddsifleet/github/planned.day.backup/models/hey-leo_en_raspberry-pi_v3_0_0/hey-leo_en_raspberry-pi_v3_0_0.ppn"
]

# Initialize Picovoice components
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=keyword_paths,
)
cheetah = pvcheetah.create(access_key=ACCESS_KEY)
cobra = pvcobra.create(access_key=ACCESS_KEY)

# Initialize recorder (uses Porcupine's frame length)
recorder = PvRecorder(
    frame_length=porcupine.frame_length,
    device_index=2,
)


def transcribe_audio(frames, sample_rate):
    """
    Transcribe recorded audio frames using Cheetah.
    """
    all_samples = []
    for frame in frames:
        all_samples.extend(frame)

    # Resample if needed
    if sample_rate != cheetah.sample_rate:
        audio_array = np.array(all_samples, dtype=np.float32)
        ratio = cheetah.sample_rate / sample_rate
        new_length = int(len(audio_array) * ratio)
        resampled = np.interp(
            np.linspace(0, len(audio_array), new_length),
            np.arange(len(audio_array)),
            audio_array,
        ).astype(np.int16)
        all_samples = resampled.tolist()

    # Process in chunks matching Cheetah's frame length
    transcript = ""
    for i in range(0, len(all_samples), cheetah.frame_length):
        chunk = all_samples[i : i + cheetah.frame_length]

        if len(chunk) < cheetah.frame_length:
            chunk = chunk + [0] * (cheetah.frame_length - len(chunk))

        partial, is_endpoint = cheetah.process(chunk)
        transcript += partial

    final = cheetah.flush()
    transcript += final

    return transcript.strip()


def record_until_silence():
    """
    Record audio until silence is detected using Cobra VAD.
    """
    print("\nListening... (speak now)")

    recorded_frames = []
    silence_start = None

    # Buffer for Cobra (may have different frame length)
    cobra_buffer = []

    while True:
        frame = recorder.read()
        recorded_frames.append(frame)

        # Accumulate samples for Cobra
        cobra_buffer.extend(frame)

        # Process when we have enough samples for Cobra
        while len(cobra_buffer) >= cobra.frame_length:
            cobra_frame = cobra_buffer[: cobra.frame_length]
            cobra_buffer = cobra_buffer[cobra.frame_length :]

            voice_probability = cobra.process(cobra_frame)

            if voice_probability < VOICE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= SILENCE_DURATION:
                    print("\nSilence detected, transcribing...")
                    return recorded_frames
            else:
                silence_start = None
                print("*", end="", flush=True)

    return recorded_frames


async def _run_loop():
    try:
        recorder.start()
        print("Waiting for wake word...")

        while True:
            frame = recorder.read()
            keyword_index = porcupine.process(frame)

            if keyword_index >= 0:
                print("\nWake word detected!")

                frames = record_until_silence()
                text = transcribe_audio(frames, porcupine.sample_rate)

                if text:
                    print(f"\nTranscription: {text}\n")
                else:
                    print("\n(No speech detected)\n")

                print("Waiting for wake word...")
            else:
                print(".", end="", flush=True)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        cheetah.delete()
        cobra.delete()


async def run_async():
    while True:
        try:
            await _run_loop()
        except Exception as e:
            logger.exception(f"Error Listening: {e}")


def run():
    asyncio.run(run_async())
