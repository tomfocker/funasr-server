from pathlib import Path
import unittest


class DockerImageLayoutTests(unittest.TestCase):
    def test_dockerfile_bakes_fun_asr_nano_model_into_image(self) -> None:
        dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("CW_MODEL_DIR=/app/Fun-ASR-Nano-GGUF", dockerfile)
        self.assertIn("CW_AUTO_DOWNLOAD_MODEL=0", dockerfile)
        self.assertIn("scripts/bootstrap_fun_asr_env.py", dockerfile)
        self.assertIn("CW_AUTO_DOWNLOAD_MODEL=1 python3 scripts/bootstrap_fun_asr_env.py", dockerfile)


if __name__ == "__main__":
    unittest.main()
