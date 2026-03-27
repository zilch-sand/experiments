#!/usr/bin/env python3
"""
Desktop app to record outgoing (microphone) and incoming (system/speaker) audio
into separate channels of a stereo audio file.

Output file layout:
- Left channel: incoming/system audio (mixed to mono if source is stereo)
- Right channel: outgoing/microphone audio (mixed to mono if source is stereo)

Supported output formats:
- WAV (lossless, broadly compatible)
- FLAC (lossless compressed)
- OGG/Vorbis (lossy compressed)
- MP3 (lossy, exported through ffmpeg)

Notes:
- On Windows, the app uses WASAPI loopback for system audio capture. Select your
  speaker/output device in the "Incoming" list.
- On macOS/Linux, system audio capture usually requires a virtual/monitor device
  such as BlackHole / Loopback / Soundflower (macOS) or PulseAudio monitor /
  PipeWire monitor sources (Linux). Select that device in the "Incoming" list.
- The app records each stream independently and then aligns/pads them when saved.
  For very long recordings on different hardware clocks, slight drift is still
  possible.

Dependencies:
    pip install sounddevice soundfile numpy
Optional for MP3:
    ffmpeg must be installed and available on PATH
"""

from __future__ import annotations

import os
import platform
import queue
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import sounddevice as sd
import soundfile as sf

APP_TITLE = "Incoming / Outgoing Audio Recorder"
DEFAULT_SR = 48000
DEFAULT_BLOCKSIZE = 1024
DEFAULT_FORMAT = "FLAC"
OUTPUT_FORMATS = ("WAV", "FLAC", "OGG", "MP3")
FILE_TYPES = {
    "WAV": [("WAV files", "*.wav")],
    "FLAC": [("FLAC files", "*.flac")],
    "OGG": [("OGG files", "*.ogg")],
    "MP3": [("MP3 files", "*.mp3")],
}
FORMAT_EXTENSIONS = {
    "WAV": ".wav",
    "FLAC": ".flac",
    "OGG": ".ogg",
    "MP3": ".mp3",
}


@dataclass
class DeviceChoice:
    index: int
    label: str
    is_output: bool
    is_input: bool
    hostapi: str
    max_input_channels: int
    max_output_channels: int

    def display(self) -> str:
        caps = []
        if self.is_input:
            caps.append(f"in:{self.max_input_channels}")
        if self.is_output:
            caps.append(f"out:{self.max_output_channels}")
        return f"[{self.index}] {self.label} ({self.hostapi}; {', '.join(caps)})"


class AudioRecorder:
    def __init__(self) -> None:
        self.sample_rate = DEFAULT_SR
        self.blocksize = DEFAULT_BLOCKSIZE
        self._mic_stream: sd.InputStream | None = None
        self._sys_stream: sd.InputStream | None = None
        self._recording = False
        self._lock = threading.Lock()
        self._mic_chunks: list[np.ndarray] = []
        self._sys_chunks: list[np.ndarray] = []
        self._status_queue: queue.Queue[str] = queue.Queue()
        self.save_path = ""
        self.output_format = DEFAULT_FORMAT

    @property
    def recording(self) -> bool:
        return self._recording

    def pop_status_messages(self) -> list[str]:
        messages: list[str] = []
        while True:
            try:
                messages.append(self._status_queue.get_nowait())
            except queue.Empty:
                break
        return messages

    def _push_status(self, msg: str) -> None:
        self._status_queue.put(msg)

    @staticmethod
    def _to_mono(indata: np.ndarray) -> np.ndarray:
        arr = np.asarray(indata, dtype=np.float32)
        # If already 1D, treat as mono and return a copy
        if arr.ndim == 1:
            return arr.copy()
        # If shape is (N, 1), squeeze to 1D
        if arr.shape[1] == 1:
            return arr[:, 0].copy()
        # Sum channels and clip to preserve signal strength without exceeding [-1.0, 1.0]
        mono = arr.sum(axis=1, dtype=np.float32)
        np.clip(mono, -1.0, 1.0, out=mono)
        return mono

    @staticmethod
    def _require_ffmpeg() -> str:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(
                "MP3 export requires ffmpeg on your PATH. Install ffmpeg, or choose WAV/FLAC/OGG."
            )
        return ffmpeg

    @classmethod
    def _write_audio_file(cls, path: str, stereo: np.ndarray, sample_rate: int, output_format: str) -> None:
        fmt = output_format.upper()
        if fmt == "WAV":
            sf.write(path, stereo, sample_rate, format="WAV", subtype="PCM_24")
        elif fmt == "FLAC":
            sf.write(path, stereo, sample_rate, format="FLAC")
        elif fmt == "OGG":
            sf.write(path, stereo, sample_rate, format="OGG", subtype="VORBIS")
        elif fmt == "MP3":
            ffmpeg = cls._require_ffmpeg()
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_wav = os.path.join(tmpdir, "tmp_audio.wav")
                sf.write(temp_wav, stereo, sample_rate, format="WAV", subtype="PCM_16")
                cmd = [
                    ffmpeg,
                    "-y",
                    "-i",
                    temp_wav,
                    "-codec:a",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    path,
                ]
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("ffmpeg timed out during MP3 export.") from exc
                if result.returncode != 0:
                    stderr = (result.stderr or "").strip()
                    raise RuntimeError(f"ffmpeg failed during MP3 export. {stderr}")
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _mic_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._push_status(f"Mic: {status}")
        mono = self._to_mono(indata)
        with self._lock:
            if self._recording:
                self._mic_chunks.append(mono)

    def _sys_callback(self, indata, frames, time_info, status) -> None:
        if status:
            self._push_status(f"Incoming: {status}")
        mono = self._to_mono(indata)
        with self._lock:
            if self._recording:
                self._sys_chunks.append(mono)

    def start(
        self,
        mic_device_index: int,
        incoming_device_index: int,
        sample_rate: int,
        save_path: str,
        output_format: str,
    ) -> None:
        if self._recording:
            raise RuntimeError("Already recording")

        self.sample_rate = int(sample_rate)
        self.save_path = save_path
        self.output_format = output_format.upper()
        self._mic_chunks = []
        self._sys_chunks = []
        self._push_status("Starting streams...")

        mic_info = sd.query_devices(mic_device_index)
        mic_channels = max(1, min(2, int(mic_info["max_input_channels"])))

        mic_kwargs = dict(
            device=mic_device_index,
            samplerate=self.sample_rate,
            channels=mic_channels,
            dtype="float32",
            blocksize=self.blocksize,
            callback=self._mic_callback,
        )

        sys_info = sd.query_devices(incoming_device_index)
        sys_channels = max(1, min(2, int(sys_info["max_input_channels"])))

        sys_kwargs = dict(
            device=incoming_device_index,
            samplerate=self.sample_rate,
            channels=sys_channels,
            dtype="float32",
            blocksize=self.blocksize,
            callback=self._sys_callback,
        )

        if platform.system() == "Windows":
            try:
                sys_kwargs["extra_settings"] = sd.WasapiSettings(loopback=True)
            except Exception:
                pass

        try:
            self._mic_stream = sd.InputStream(**mic_kwargs)
            self._sys_stream = sd.InputStream(**sys_kwargs)
            self._mic_stream.start()
            self._sys_stream.start()
        except Exception:
            self._cleanup_streams()
            raise

        self._recording = True
        self._push_status(f"Recording to {self.output_format}...")

    def stop(self) -> str:
        if not self._recording:
            raise RuntimeError("Not currently recording")

        with self._lock:
            self._recording = False
        self._cleanup_streams()

        # Snapshot chunks and configuration under lock to avoid races with callbacks.
        with self._lock:
            mic_chunks = list(self._mic_chunks)
            sys_chunks = list(self._sys_chunks)

        # Preserve original behavior: if no audio was captured, raise on the calling thread.
        if not mic_chunks and not sys_chunks:
            raise RuntimeError("No audio captured")

        save_path = self.save_path
        sample_rate = self.sample_rate
        output_format = self.output_format

        # Perform potentially slow processing and file I/O on a background thread
        # so the UI/main thread is not blocked.
        worker = threading.Thread(
            target=self._process_and_save_recording,
            args=(mic_chunks, sys_chunks, save_path, sample_rate, output_format),
            daemon=True,
        )
        worker.start()

        return save_path

    def _process_and_save_recording(
        self,
        mic_chunks: list[np.ndarray],
        sys_chunks: list[np.ndarray],
        save_path: str | Path,
        sample_rate: int,
        output_format: str,
    ) -> None:
        """Reconstruct and save the recording on a background thread."""
        try:
            mic = np.concatenate(mic_chunks) if mic_chunks else np.zeros(0, dtype=np.float32)
            sysa = np.concatenate(sys_chunks) if sys_chunks else np.zeros(0, dtype=np.float32)

            n = max(len(mic), len(sysa))
            if n == 0:
                # Should already have been checked in stop(), but guard defensively.
                self._push_status("No audio captured; nothing to save.")
                return

            if len(mic) < n:
                mic = np.pad(mic, (0, n - len(mic)))
            if len(sysa) < n:
                sysa = np.pad(sysa, (0, n - len(sysa)))

            stereo = np.column_stack([sysa, mic]).astype(np.float32)
            self._write_audio_file(save_path, stereo, sample_rate, output_format)
            self._push_status(f"Saved {output_format}: {save_path}")
        except Exception as exc:
            # Report failure via status; exceptions here cannot be propagated
            # back to the UI thread directly.
            self._push_status(f"Error while saving recording: {exc}")
    def _cleanup_streams(self) -> None:
        for stream in (self._mic_stream, self._sys_stream):
            if stream is None:
                continue
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass
        self._mic_stream = None
        self._sys_stream = None


class RecorderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("880x660")
        self.root.minsize(760, 540)

        self.recorder = AudioRecorder()
        self.devices = self._load_devices()
        self.device_lookup = {d.display(): d for d in self.devices}

        self._build_ui()
        self._set_defaults()
        self._poll_status_queue()

    def _load_devices(self) -> list[DeviceChoice]:
        hostapis = sd.query_hostapis()
        raw_devices = sd.query_devices()
        devices: list[DeviceChoice] = []
        for idx, d in enumerate(raw_devices):
            hostapi_name = hostapis[d["hostapi"]]["name"]
            devices.append(
                DeviceChoice(
                    index=idx,
                    label=d["name"],
                    is_output=bool(d["max_output_channels"] > 0),
                    is_input=bool(d["max_input_channels"] > 0),
                    hostapi=hostapi_name,
                    max_input_channels=int(d["max_input_channels"]),
                    max_output_channels=int(d["max_output_channels"]),
                )
            )
        return devices

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer,
            text="Record mic/outgoing and system/incoming audio to separate channels",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(outer, text="Outgoing device (microphone):").grid(row=1, column=0, sticky="w", **pad)
        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(outer, textvariable=self.mic_var, state="readonly", width=90)
        self.mic_combo["values"] = [d.display() for d in self.devices if d.is_input]
        self.mic_combo.grid(row=1, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(outer, text="Incoming device (system/output or monitor):").grid(row=2, column=0, sticky="w", **pad)
        self.sys_var = tk.StringVar()
        self.sys_combo = ttk.Combobox(outer, textvariable=self.sys_var, state="readonly", width=90)
        self.sys_combo["values"] = self._incoming_device_values()
        self.sys_combo.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(outer, text="Sample rate:").grid(row=3, column=0, sticky="w", **pad)
        self.sr_var = tk.StringVar(value=str(DEFAULT_SR))
        self.sr_combo = ttk.Combobox(outer, textvariable=self.sr_var, state="readonly", width=12)
        self.sr_combo["values"] = ["44100", "48000", "96000"]
        self.sr_combo.grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(outer, text="Output format:").grid(row=4, column=0, sticky="w", **pad)
        self.format_var = tk.StringVar(value=DEFAULT_FORMAT)
        self.format_combo = ttk.Combobox(outer, textvariable=self.format_var, state="readonly", width=12)
        self.format_combo["values"] = list(OUTPUT_FORMATS)
        self.format_combo.grid(row=4, column=1, sticky="w", **pad)
        self.format_combo.bind("<<ComboboxSelected>>", self._on_format_change)

        ttk.Label(outer, text="Output file:").grid(row=5, column=0, sticky="w", **pad)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(outer, textvariable=self.path_var)
        self.path_entry.grid(row=5, column=1, sticky="ew", **pad)
        self.path_button = ttk.Button(outer, text="Browse", command=self._choose_save_path)
        self.path_button.grid(row=5, column=2, sticky="e", **pad)

        controls = ttk.Frame(outer)
        controls.grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        self.start_button = ttk.Button(controls, text="Start recording", command=self._start_recording)
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = ttk.Button(controls, text="Stop and save", command=self._stop_recording, state="disabled")
        self.stop_button.pack(side="left")

        self.status_var = tk.StringVar(value="Idle")
        status_label = ttk.Label(outer, textvariable=self.status_var)
        status_label.grid(row=7, column=0, columnspan=3, sticky="w", **pad)

        help_text = self._help_text()
        ttk.Label(outer, text="Notes:").grid(row=8, column=0, sticky="nw", **pad)
        self.help_box = tk.Text(outer, height=10, wrap="word")
        self.help_box.grid(row=8, column=1, columnspan=2, sticky="nsew", **pad)
        self.help_box.insert("1.0", help_text)
        self.help_box.configure(state="disabled")

        ttk.Label(outer, text="Log:").grid(row=9, column=0, sticky="nw", **pad)
        self.log_box = tk.Text(outer, height=12, wrap="word")
        self.log_box.grid(row=9, column=1, columnspan=2, sticky="nsew", **pad)

        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(9, weight=1)

    def _incoming_device_values(self) -> list[str]:
        if platform.system() == "Windows":
            return [d.display() for d in self.devices if d.is_output]

        preferred = [
            d.display() for d in self.devices
            if d.is_input and any(keyword in d.label.lower() for keyword in ("blackhole", "loopback", "monitor", "soundflower", "pulse", "pipewire"))
        ]
        others = [d.display() for d in self.devices if d.is_input and d.display() not in preferred]
        return preferred + others

    def _help_text(self) -> str:
        format_notes = (
            "Output formats:\n"
            "- WAV: uncompressed, largest files\n"
            "- FLAC: lossless compressed, smaller files\n"
            "- OGG: lossy compressed, usually smallest files\n"
            "- MP3: lossy compressed, broad compatibility, requires ffmpeg\n\n"
        )
        if platform.system() == "Windows":
            return (
                "Windows: choose a microphone for outgoing audio and your speakers/headphones "
                "for incoming audio. The app uses WASAPI loopback to capture the selected "
                "output device.\n\n"
                + format_notes +
                "Saved channel layout:\n"
                "- Left channel = incoming/system audio\n"
                "- Right channel = outgoing/microphone audio\n\n"
                "If a source is stereo, it is mixed to mono before being written to its side."
            )
        return (
            "macOS/Linux: system audio capture usually needs a virtual or monitor input. "
            "Examples: BlackHole / Loopback / Soundflower on macOS, or monitor sources on "
            "PulseAudio/PipeWire Linux. Select that virtual input as the incoming device.\n\n"
            + format_notes +
            "Saved channel layout:\n"
            "- Left channel = incoming/system audio\n"
            "- Right channel = outgoing/microphone audio\n\n"
            "If a source is stereo, it is mixed to mono before being written to its side."
        )

    def _default_output_path(self, output_format: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = FORMAT_EXTENSIONS[output_format.upper()]
        return Path.cwd() / f"audio_recording_{timestamp}{ext}"

    def _set_defaults(self) -> None:
        input_defaults = [d.display() for d in self.devices if d.is_input]
        incoming_defaults = self._incoming_device_values()
        if input_defaults:
            self.mic_var.set(input_defaults[0])
        if incoming_defaults:
            self.sys_var.set(incoming_defaults[0])
        self.path_var.set(str(self._default_output_path(self.format_var.get())))

    def _on_format_change(self, _event=None) -> None:
        current = self.path_var.get().strip()
        fmt = self.format_var.get().upper()
        desired_ext = FORMAT_EXTENSIONS[fmt]
        if fmt == "MP3" and not shutil.which("ffmpeg"):
            messagebox.showwarning(
                APP_TITLE,
                "MP3 export requires ffmpeg on your PATH.\n"
                "Install ffmpeg or choose a different format.",
            )
        if not current:
            self.path_var.set(str(self._default_output_path(fmt)))
            return
        path = Path(current)
        if path.suffix.lower() in {".wav", ".flac", ".ogg", ".mp3"}:
            path = path.with_suffix(desired_ext)
            self.path_var.set(str(path))

    def _choose_save_path(self) -> None:
        fmt = self.format_var.get().upper()
        path = filedialog.asksaveasfilename(
            title="Save recording as",
            defaultextension=FORMAT_EXTENSIONS[fmt],
            filetypes=FILE_TYPES[fmt],
            initialfile=Path(self.path_var.get()).name or f"recording{FORMAT_EXTENSIONS[fmt]}",
        )
        if path:
            self.path_var.set(path)

    def _selected_device(self, combo_var: tk.StringVar) -> DeviceChoice:
        selected = combo_var.get().strip()
        if selected not in self.device_lookup:
            raise ValueError("Please select a valid device")
        return self.device_lookup[selected]

    def _start_recording(self) -> None:
        try:
            mic = self._selected_device(self.mic_var)
            incoming = self._selected_device(self.sys_var)
            sample_rate = int(self.sr_var.get())
            output_format = self.format_var.get().upper()
            save_path = self.path_var.get().strip()

            if not save_path:
                raise ValueError("Please choose an output file")
            out_dir = os.path.dirname(os.path.abspath(save_path)) or "."
            if not os.path.isdir(out_dir):
                raise ValueError("Output folder does not exist")

            ext = Path(save_path).suffix.lower()
            expected_ext = FORMAT_EXTENSIONS[output_format]
            if ext != expected_ext:
                save_path = str(Path(save_path).with_suffix(expected_ext))
                self.path_var.set(save_path)

            self.recorder.start(
                mic_device_index=mic.index,
                incoming_device_index=incoming.index,
                sample_rate=sample_rate,
                save_path=save_path,
                output_format=output_format,
            )
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not start recording:\n\n{e}")
            self._append_log(f"ERROR starting: {e}")
            return

        self.status_var.set("Recording")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._append_log(f"Recording started ({output_format})")

    def _stop_recording(self) -> None:
        try:
            saved_path = self.recorder.stop()
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not stop/save recording:\n\n{e}")
            self._append_log(f"ERROR stopping: {e}")
            self.status_var.set("Error")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return

        self.status_var.set("Saved")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._append_log(f"Saved recording to {saved_path}")
        messagebox.showinfo(APP_TITLE, f"Saved recording:\n\n{saved_path}")

    def _append_log(self, msg: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{stamp}] {msg}\n")
        self.log_box.see("end")

    def _poll_status_queue(self) -> None:
        for msg in self.recorder.pop_status_messages():
            self.status_var.set(msg)
            self._append_log(msg)
        self.root.after(100, self._poll_status_queue)


def main() -> None:
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = RecorderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
