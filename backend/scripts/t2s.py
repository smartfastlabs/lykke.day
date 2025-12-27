from array import array

import pvorca
import pyaudio

ACCESS_KEY = "peRaidcVma8bYAHuxjPa5oJ0mp/1+dTpCTcFA31k+cRVRaDHpy4VCQ=="

orca = pvorca.create(access_key=ACCESS_KEY)


def text_generator():
    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Please adjust the volume and speed to find the clearest sound.",
        "Artificial intelligence is improving the way we interact with technology.",
        "This is a simple test to check pronunciation and pacing.",
    ]

    for text in texts:
        yield text


def main():
    # Set up audio output with PyAudio
    p = pyaudio.PyAudio()

    # Orca outputs mono 16-bit PCM; sample rate is exposed on the orca object
    stream_out = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=orca.sample_rate,
        output=True,
    )

    # Use streaming mode
    orca_stream = orca.stream_open()

    try:
        # Stream text -> audio
        for text_chunk in text_generator():
            pcm = orca_stream.synthesize(text_chunk)
            if pcm is not None:
                # pcm is a sequence of int16 samples; convert to bytes for PyAudio
                pcm_bytes = array("h", pcm).tobytes()
                stream_out.write(pcm_bytes)

        # Flush remaining buffered audio
        pcm = orca_stream.flush()
        if pcm is not None:
            pcm_bytes = array("h", pcm).tobytes()
            stream_out.write(pcm_bytes)

    finally:
        # Cleanup
        orca_stream.close()
        orca.delete()
        stream_out.stop_stream()
        stream_out.close()
        p.terminate()


if __name__ == "__main__":
    main()
