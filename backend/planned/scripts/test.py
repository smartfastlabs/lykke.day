import struct
import webrtcvad
import time
import numpy as np
import pvporcupine
import pvcheetah
import pyaudio

ACCESS_KEY = "peRaidcVma8bYAHuxjPa5oJ0mp/1+dTpCTcFA31k+cRVRaDHpy4VCQ=="

# Configuration
SILENCE_THRESHOLD = 500  # Adjust based on your mic/environment (RMS amplitude)
SILENCE_DURATION = 1.0   # Seconds of silence before processing

keyword_paths = [
    "/home/toddsifleet/github/planned.day.backup/models/hey-leo_en_raspberry-pi_v3_0_0/hey-leo_en_raspberry-pi_v3_0_0.ppn"
]

handle = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=keyword_paths)
cheetah = pvcheetah.create(access_key=ACCESS_KEY)

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


vad = webrtcvad.Vad(2)  # Aggressiveness: 0-3 (3 = most aggressive filtering)

def record_until_silence():
    print("\nListening... (speak now)")
    
    recorded_frames = []
    silence_start = None
    
    # WebRTC VAD requires 10, 20, or 30ms frames at 8/16/32/48kHz
    # Porcupine's frame length may differ, so we accumulate samples
    samples_per_vad_frame = int(handle.sample_rate * 0.03)  # 30ms
    sample_buffer = []
    
    while True:
        frame = get_next_audio_frame()
        recorded_frames.append(frame)
        sample_buffer.extend(frame)
        
        # Process when we have enough for VAD
        while len(sample_buffer) >= samples_per_vad_frame:
            vad_frame = sample_buffer[:samples_per_vad_frame]
            sample_buffer = sample_buffer[samples_per_vad_frame:]
            
            # Convert to bytes for webrtcvad
            audio_bytes = struct.pack(f"{len(vad_frame)}h", *vad_frame)
            is_speech = vad.is_speech(audio_bytes, handle.sample_rate)
            
            if not is_speech:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= SILENCE_DURATION:
                    print("\nSilence detected, transcribing...")
                    return recorded_frames
            else:
                silence_start = None
                print("*", end="", flush=True)
    
    return recorded_frames

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


def transcribe_audio(frames, sample_rate):
    """
    Transcribe recorded audio frames using Cheetah.
    Resamples if necessary to match Cheetah's expected sample rate.
    """
    # Flatten all frames into a single array
    all_samples = []
    for frame in frames:
        all_samples.extend(frame)
    
    # Resample if Cheetah expects a different sample rate
    if sample_rate != cheetah.sample_rate:
        audio_array = np.array(all_samples, dtype=np.float32)
        ratio = cheetah.sample_rate / sample_rate
        new_length = int(len(audio_array) * ratio)
        resampled = np.interp(
            np.linspace(0, len(audio_array), new_length),
            np.arange(len(audio_array)),
            audio_array
        ).astype(np.int16)
        all_samples = resampled.tolist()
    
    # Process in chunks matching Cheetah's frame length
    transcript = ""
    for i in range(0, len(all_samples), cheetah.frame_length):
        chunk = all_samples[i:i + cheetah.frame_length]
        
        # Pad the last chunk if necessary
        if len(chunk) < cheetah.frame_length:
            chunk = chunk + [0] * (cheetah.frame_length - len(chunk))
        
        partial, is_endpoint = cheetah.process(chunk)
        transcript += partial
    
    # Flush to get any remaining transcription
    final = cheetah.flush()
    transcript += final
    
    return transcript.strip()




try:
    print("Waiting for wake word...")
    
    while True:
        keyword_index = handle.process(get_next_audio_frame())
        
        if keyword_index >= 0:
            print("\nWake word detected!")
            
            # Record until silence
            frames = record_until_silence()
            
            # Transcribe the recording
            text = transcribe_audio(frames, handle.sample_rate)
            
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
    if audio_stream is not None:
        audio_stream.stop_stream()
        audio_stream.close()
    pa.terminate()
    handle.delete()
    cheetah.delete()