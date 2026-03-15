#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import textwrap
import urllib.request
from dataclasses import dataclass

OWNER = "jatinchowdhury18"
REPO = "AnalogTapeModel"
COMMIT = "604372e4ffd9690c3e283362e4598cb43edbb475"
RAW_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{COMMIT}"


@dataclass(frozen=True)
class Stage:
    needle: str
    description: str


PROCESS_STAGES = [
    Stage("dryBuffer.makeCopyOf", "Copy the untouched input into a parallel dry path for later dry/wet mixing."),
    Stage("inGain.processBlock", "Apply the user-controlled input gain before the tape model."),
    Stage("inputFilters.processBlockMakeup", "Optionally add the removed low/high bands back into the post-latency-compensated signal."),
    Stage("inputFilters.processBlock", "Apply optional input high-pass / low-pass filtering and capture the removed bands for optional makeup."),
    Stage("scope->pushSamplesIO (buffer, TapeScope::AudioType::Input)", "Send the pre-tape signal to the visualizer."),
    Stage("midSideController.processInput", "Optionally convert stereo to mid/side and apply stereo balance before the nonlinear stages."),
    Stage("toneControl.processBlockIn", "Apply the pre-emphasis tone stage before the tape core."),
    Stage("compressionProcessor.processBlock", "Apply input compression with oversampled gain reduction."),
    Stage("hysteresis.processBlock", "Run the core tape hysteresis model that generates saturation, bias-related behavior, and memory effects."),
    Stage("toneControl.processBlockOut", "Apply the complementary de-emphasis tone stage after hysteresis."),
    Stage("chewer.processBlock", "Add intermittent tape-chew/dropout style damage."),
    Stage("degrade.processBlock", "Add noise, bandwidth loss, and level-dependent degradation."),
    Stage("flutter.processBlock", "Apply wow and flutter as a time-varying delay modulation."),
    Stage("lossFilter.processBlock", "Apply playback-head loss filters and azimuth mismatch."),
    Stage("latencyCompensation()", "Delay the dry path and filter-makeup path so they stay phase-aligned with the wet path."),
    Stage("midSideController.processOutput", "Decode back from mid/side and undo stereo balance makeup if enabled."),
    Stage("outGain.processBlock", "Apply output gain."),
    Stage("dryWet.processBlock", "Blend the delayed dry path with the processed wet path."),
    Stage("chowdsp::BufferMath::sanitizeBuffer", "Clean up NaNs/denormals before output."),
    Stage("scope->pushSamplesIO (buffer, TapeScope::AudioType::Output)", "Send the final post-tape signal to the visualizer."),
]


def fetch_text(path: str) -> str:
    url = f"{RAW_BASE}/{path}"
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def extract_between(text: str, start: str, end: str) -> tuple[int, list[str]]:
    lines = text.splitlines()
    start_index = next((i for i, line in enumerate(lines) if start in line), None)
    if start_index is None:
        raise SystemExit(f"start marker not found: {start!r}")

    if end == "__EOF__":
        end_index = len(lines)
    else:
        end_index = next((i for i in range(start_index + 1, len(lines)) if end in lines[i]), None)
        if end_index is None:
            raise SystemExit(f"end marker not found after start marker: {end!r}")

    return start_index + 1, lines[start_index:end_index]


def print_numbered(lines: list[str], start_line: int) -> None:
    for offset, line in enumerate(lines):
        print(f"{start_line + offset:4}: {line}")


def command_stage_order(_: argparse.Namespace) -> None:
    text = fetch_text("Plugin/Source/PluginProcessor.cpp")
    start_line, lines = extract_between(
        text,
        "void ChowtapeModelAudioProcessor::processAudioBlock",
        "void ChowtapeModelAudioProcessor::latencyCompensation",
    )

    print(f"AnalogTapeModel commit: {COMMIT}")
    print("Signal path inside processAudioBlock():")

    stage_no = 1
    for offset, line in enumerate(lines):
        stripped = line.strip()
        for stage in PROCESS_STAGES:
            if stage.needle in stripped:
                print(f"{stage_no:2}. L{start_line + offset}: {stripped}")
                print(textwrap.indent(stage.description, prefix="    "))
                stage_no += 1
                break


def command_snippet(args: argparse.Namespace) -> None:
    text = fetch_text(args.path)
    start_line, lines = extract_between(text, args.start, args.end)
    print(f"{args.path} @ {COMMIT}")
    print_numbered(lines, start_line)


def command_matches(args: argparse.Namespace) -> None:
    text = fetch_text(args.path)
    pattern = re.compile(args.pattern)
    print(f"{args.path} @ {COMMIT}")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            print(f"{line_no:4}: {line}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch stable AnalogTapeModel snippets for the walkthrough.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stage_parser = subparsers.add_parser("stage-order", help="Print the ordered audio path from processAudioBlock().")
    stage_parser.set_defaults(func=command_stage_order)

    snippet_parser = subparsers.add_parser("snippet", help="Print a numbered snippet between two markers.")
    snippet_parser.add_argument("path", help="Repository path relative to the AnalogTapeModel root.")
    snippet_parser.add_argument("start", help="Substring that marks the first line to include.")
    snippet_parser.add_argument("end", help="Substring that marks the first line after the snippet.")
    snippet_parser.set_defaults(func=command_snippet)

    matches_parser = subparsers.add_parser("matches", help="Print numbered lines that match a regex.")
    matches_parser.add_argument("path", help="Repository path relative to the AnalogTapeModel root.")
    matches_parser.add_argument("pattern", help="Python regex to search for.")
    matches_parser.set_defaults(func=command_matches)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
