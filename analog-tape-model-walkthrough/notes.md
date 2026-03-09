# Notes

## Goal
Create a Showboat-based linear walkthrough of the DSP/audio-processing code in jatinchowdhury18/AnalogTapeModel for readers who know audio engineering and Python-level programming, but not C++.

## 2026-03-09
- Ran `python -m pip install -r requirements.txt` at the repo root to confirm the existing documentation tooling setup.
- Ran `cog -r -P README.md` as part of understanding the repo's current automation; reverted the resulting unrelated README churn.
- Installed `uv` and ran `uvx showboat --help` successfully to confirm Showboat is available in this environment.
- Next steps: inspect AnalogTapeModel via GitHub APIs, identify the audio path, then build a Showboat document plus README report in this folder.
- Identified the linear DSP order directly from `Plugin/Source/PluginProcessor.cpp` in AnalogTapeModel.
- Pulled the core DSP implementation files from the upstream repository via raw GitHub URLs pinned to commit `604372e4ffd9690c3e283362e4598cb43edbb475`.
- Wrote `analog_tape_tools.py` to fetch stable upstream snippets with line numbers for the walkthrough.
- Built `demo.md` with Showboat so the walkthrough includes both commentary and executable code-snippet extraction.
- Key architectural takeaway: the plugin is organized as a serial wet path with a parallel dry path kept for latency-aligned dry/wet mixing at the end.
