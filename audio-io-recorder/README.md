# Separate call recorder

This Python desktop app records:
- **incoming/system audio** to the **left** channel
- **outgoing/microphone audio** to the **right** channel

If either source is stereo, it is mixed down to mono before being written to its side of the stereo file.

## Features
- device selection GUI
- separate channel recording
- sample-rate selection
- compressed output format selection
- MP3 export via ffmpeg

## Output formats
- **WAV** — uncompressed, largest files
- **FLAC** — lossless compression, good default for smaller files without quality loss
- **OGG/Vorbis** — lossy compression, usually the smallest files
- **MP3** — lossy compression with broad compatibility; exported through ffmpeg

## Install

```bash
pip install sounddevice soundfile numpy
```

For **MP3** output, install **ffmpeg** and make sure `ffmpeg` is available on your system `PATH`.

## Run

```bash
python separate_call_recorder.py
```

## Platform notes

### Windows
- Select your **microphone** as the outgoing device.
- Select your **speakers/headphones output device** as the incoming device.
- The app uses **WASAPI loopback** to capture the selected output device.

### macOS / Linux
System-output capture usually needs a virtual or monitor device.
Examples:
- **macOS:** BlackHole, Loopback, Soundflower
- **Linux:** PulseAudio monitor source, PipeWire monitor source

Select that monitor/virtual device as the incoming device.

## Saved channel layout
- **Left** = incoming/system audio
- **Right** = outgoing/microphone audio

## Notes
- The app records the two streams independently, then aligns and pads them when saving.
- For very long recordings on different hardware clocks, slight drift may still occur.
- FLAC and OGG support depend on the local `libsndfile` build used by `soundfile`.
- MP3 export requires `ffmpeg`. If MP3 save fails, try WAV or FLAC first, or verify ffmpeg is installed and on PATH.
