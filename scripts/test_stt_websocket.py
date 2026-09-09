from __future__ import annotations

"""WebSocket STT integration test.

Streams a 16 kHz mono WAV over /ws/audio in chunks and prints the transcript.

Usage:
  python scripts/test_stt_websocket.py --wav path/to/test.wav

Default sample: scripts/fixtures/test_phrase_16k.wav
"""

import argparse
import asyncio
import json
import sys
import wave
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Install websockets: pip install websockets", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WAV = ROOT / "scripts" / "fixtures" / "test_phrase_16k.wav"
DEFAULT_EXPECTED = "I would like to book an appointment"

URL = "ws://127.0.0.1:8000/ws/audio"
CHUNK_SIZE = 4096


def validate_wav(path: Path) -> None:
    with wave.open(str(path), "rb") as wf:
        if wf.getnchannels() != 1:
            raise SystemExit(f"{path}: expected mono WAV")
        if wf.getframerate() != 16000:
            raise SystemExit(
                f"{path}: expected 16 kHz WAV (ffmpeg: ffmpeg -i in.wav -ar 16000 -ac 1 out.wav)"
            )


async def run(wav_path: Path, expected: str | None) -> None:
    if not wav_path.is_file():
        raise SystemExit(
            f"Missing {wav_path}. Run: python scripts/create_test_wav.py "
            "or pass --wav to a 16 kHz mono file."
        )
    validate_wav(wav_path)
    audio = wav_path.read_bytes()

    async with websockets.connect(URL) as ws:
        offset = 0
        while offset < len(audio):
            chunk = audio[offset : offset + CHUNK_SIZE]
            await ws.send(chunk)
            offset += len(chunk)

        await ws.send(json.dumps({"type": "end_of_utterance"}))
        raw = await ws.recv()
        payload = json.loads(raw)

    if payload.get("type") == "error":
        raise SystemExit(f"Server error: {payload.get('message')}")

    if payload.get("type") != "transcript":
        raise SystemExit(f"Unexpected response: {payload}")

    text = payload.get("text", "")
    call_id = payload.get("call_id")
    print(f"call_id: {call_id}")
    print(f"transcript: {text!r}")

    if expected:
        print(f"expected:   {expected!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="WebSocket STT integration test")
    parser.add_argument(
        "--wav",
        type=Path,
        default=DEFAULT_WAV,
        help="Path to 16 kHz mono PCM WAV",
    )
    parser.add_argument(
        "--expected",
        default=DEFAULT_EXPECTED,
        help="Reference phrase for manual comparison",
    )
    parser.add_argument(
        "--no-expected",
        action="store_true",
        help="Do not print reference expected text",
    )
    args = parser.parse_args()
    expected = None if args.no_expected else args.expected
    asyncio.run(run(args.wav, expected))


if __name__ == "__main__":
    main()
