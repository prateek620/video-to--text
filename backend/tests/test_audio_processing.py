from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from app.services.audio_processing import extract_audio


class ExtractAudioTests(unittest.TestCase):
    def test_extract_audio_wraps_ffmpeg_called_process_error(self) -> None:
        ffmpeg_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffmpeg", "-i", "input.mp4"],
            stderr="ffmpeg failed",
        )
        with (
            patch("app.services.audio_processing.shutil.which", return_value="ffmpeg"),
            patch("app.services.audio_processing.ensure_dir"),
            patch("app.services.audio_processing.settings.audio_dir", Path("/tmp/audio")),
            patch("app.services.audio_processing.subprocess.run", side_effect=ffmpeg_error),
        ):
            with self.assertRaisesRegex(RuntimeError, "ffmpeg failed to extract audio from input.mp4: ffmpeg failed"):
                extract_audio(Path("/tmp/input.mp4"))


if __name__ == "__main__":
    unittest.main()
