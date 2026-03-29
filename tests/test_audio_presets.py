import tempfile
import os
from mcp_video import audio_preset

def test_drone_ominous_preset():
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "drone.wav")
        result = audio_preset("drone-ominous", output, duration=2.0)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0
        print(f"✓ drone-ominous created: {os.path.getsize(result)} bytes")

if __name__ == "__main__":
    test_drone_ominous_preset()
