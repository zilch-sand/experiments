# AnalogTapeModel DSP Walkthrough

This experiment documents the **audio-processing code path** in [jatinchowdhury18/AnalogTapeModel](https://github.com/jatinchowdhury18/AnalogTapeModel) and ignores the plugin wrappers and GUI. The walkthrough is aimed at readers who understand DSP/audio engineering and can read Python comfortably, but do not yet think in C++.

## What this experiment contains

- `demo.md` — a Showboat walkthrough that explains the signal path and embeds executable snippet extraction commands
- `analog_tape_tools.py` — a small helper that fetches code snippets from a pinned AnalogTapeModel commit and prints them with line numbers
- `notes.md` — working notes captured during the investigation

## Upstream revision used

The walkthrough pins AnalogTapeModel to commit:

- `604372e4ffd9690c3e283362e4598cb43edbb475`

That keeps the code excerpts stable and makes the Showboat document reproducible.

## Main DSP takeaway

The plugin is easiest to understand if you treat it as a **linear wet-path chain** plus a **parallel dry path**:

1. Input gain
2. Input filters
3. Mid/side and stereo balance handling
4. Pre-emphasis tone stage
5. Compression
6. Hysteresis tape core
7. Complementary post-emphasis tone stage
8. Tape-damage layers (`Chew`, `Degrade`)
9. Wow/flutter time-base modulation
10. Playback-head loss filtering and azimuth
11. Output gain
12. Dry/wet recombination with latency compensation

The most important conceptual point is that **the hysteresis solver is only one stage** in the overall machine model. The plugin also models motion instability, playback losses, and defect/noise layers around that core.

## Why Showboat helped here

Showboat made it possible to build a walkthrough that is both:

- **readable** as a narrative explanation of the DSP path, and
- **verifiable** because the code blocks re-fetch and print the exact upstream snippets they discuss.

Instead of pasting large chunks of third-party code into this repo, the demo pulls only the specific functions needed for the explanation.

## Verification

The main validation step for this experiment is:

```bash
~/.local/bin/uvx showboat verify /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/demo.md
```

That re-runs every code block in the walkthrough and confirms the recorded outputs still match.

## Most useful reading order

If you want to repeat the investigation manually, the best order is:

1. `Plugin/Source/PluginProcessor.cpp` for the full stage ordering
2. `InputFilters`, `MidSideProcessor`, `ToneControl` for preconditioning
3. `CompressionProcessor`
4. `HysteresisProcessor` and `HysteresisProcessing`
5. `Chew`, `Degrade`, `WowFlutterProcessor`
6. `LossFilter` and `AzimuthProc`
7. `latencyCompensation()` and `DryWetProcessor`

That sequence mirrors the real signal path and is the same order used in `demo.md`.
