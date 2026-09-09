"""Generate 16 kHz mono test WAV for STT (Windows SAPI + resample)."""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "scripts" / "fixtures"
RAW = FIXTURES / "test_phrase.wav"
OUT = FIXTURES / "test_phrase_16k.wav"
PHRASE = "I would like to book an appointment"


def get_phrase_from_args() -> str:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--phrase", type=str, help="Phrase to synthesize", default=None)
    args, _ = parser.parse_known_args()
    return args.phrase or PHRASE


def synthesize_windows_sapi(path: Path, phrase: str) -> None:
    if sys.platform != "win32":
        raise SystemExit("On non-Windows, place a 16 kHz mono WAV at scripts/fixtures/test_phrase_16k.wav")
    try:
        import comtypes.client  # noqa: PLC0415

        voice = comtypes.client.CreateObject("SAPI.SpVoice")
        stream = comtypes.client.CreateObject("SAPI.SpFileStream")
        stream.Open(str(path), 3)  # SSFMCreateForWrite
        voice.AudioOutputStream = stream
        voice.Speak(phrase)
        stream.Close()
    except Exception:
        # Fallback: try pyttsx3 if comtypes/SAPI not available
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.save_to_file(phrase, str(path))
            engine.runAndWait()
        except Exception as e:
            raise ImportError("TTS synthesis failed: " + str(e)) from e


def resample_to_16k_mono(in_path: Path, out_path: Path) -> None:
    with wave.open(str(in_path), "rb") as wf:
        if wf.getnchannels() != 1:
            raise SystemExit("Expected mono input")
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    target_len = int(len(samples) * 16000 / rate)
    idx = np.linspace(0, len(samples) - 1, target_len)
    resampled = np.interp(idx, np.arange(len(samples)), samples)
    pcm = (np.clip(resampled, -1.0, 1.0) * 32767).astype(np.int16)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm.tobytes())


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    phrase = get_phrase_from_args()

    # Always synthesize when a custom phrase was provided to avoid stale cached audio.
    should_synthesize = (not RAW.is_file()) or (phrase != PHRASE)

    print(f"Requested phrase: {phrase}")

    if should_synthesize:
        print("Synthesizing WAV via Windows SAPI with phrase above...")
        try:
            synthesize_windows_sapi(RAW, phrase)
        except ImportError:
            raise SystemExit(
                "Install comtypes (pip install comtypes) or add scripts/fixtures/test_phrase_16k.wav manually"
            ) from None
    else:
        print("Using existing raw WAV (no custom phrase provided and RAW exists)")
    resample_to_16k_mono(RAW, OUT)
    print(f"Wrote {OUT} (phrase: {phrase})")


if __name__ == "__main__":
    main()
