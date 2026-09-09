from pathlib import Path
import wave
import contextlib
import sys


def inspect(path: Path) -> None:
    if not path.exists():
        print(f"Missing: {path}")
        return
    size = path.stat().st_size
    with contextlib.closing(wave.open(str(path), 'rb')) as wf:
        nch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fr = wf.getframerate()
        nframes = wf.getnframes()
        duration = nframes / float(fr)
    print(f"File: {path}")
    print(f"  Size bytes: {size}")
    print(f"  Channels: {nch}")
    print(f"  Sample width bytes: {sampwidth}")
    print(f"  Frame rate: {fr}")
    print(f"  Frames: {nframes}")
    print(f"  Duration sec: {duration:.3f}")


def main():
    root = Path(__file__).resolve().parents[1]
    fixtures = root / 'scripts' / 'fixtures'
    files = [
        fixtures / 'test_phrase.wav',
        fixtures / 'test_phrase_16k.wav',
    ]
    for f in files:
        inspect(f)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for p in sys.argv[1:]:
            inspect(Path(p))
    else:
        main()
import wave
from pathlib import Path

paths = [Path('scripts/fixtures/test_phrase_16k.wav'), Path('scripts/fixtures/test_phrase.wav')]

for p in paths:
    if p.exists():
        st = p.stat()
        print(f"{p}: size={st.st_size} bytes, mtime={st.st_mtime}")
        try:
            with wave.open(str(p), 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                dur = frames / rate
                nch = wf.getnchannels()
                samp = wf.getsampwidth()
            print(f"  channels={nch}, rate={rate}, frames={frames}, duration={dur:.3f} s, sampwidth={samp}")
        except wave.Error as e:
            print('  not a valid WAV:', e)
    else:
        print(f"{p}: MISSING")
