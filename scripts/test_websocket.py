"""Phase 1 echo test — superseded by scripts/test_stt_websocket.py in Phase 2."""

import sys

print(
    "The /ws/audio endpoint no longer echoes bytes.\n"
    "Use: python scripts/test_stt_websocket.py",
    file=sys.stderr,
)
sys.exit(1)
