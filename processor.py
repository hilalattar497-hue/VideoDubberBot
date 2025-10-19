# processor.py
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

PYTHON = sys.executable  # ensures same Python interpreter

def process_video(input_path: str, target_lang: str, timeout: int = 1800) -> str:
    """
    Runs video_dubber_plus.py in non-interactive mode:
      python video_dubber_plus.py <input> <output> <lang>
    Returns absolute path to the produced output file.
    Raises RuntimeError on failure.
    """
    input_p = Path(input_path)
    if not input_p.exists():
        raise FileNotFoundError("Input file not found: " + str(input_path))

    # prepare a temp output path
    tmpdir = Path(tempfile.mkdtemp(prefix="tgvdub_"))
    out_name = f"dubbed_{input_p.stem}_{target_lang}.mp4"
    output_p = tmpdir / out_name

    script = Path(__file__).parent / "video_dubber_plus.py"
    if not script.exists():
        raise FileNotFoundError("video_dubber_plus.py not found next to processor.py")

    cmd = [PYTHON, str(script), str(input_p), str(output_p), target_lang]

    # run the script (capture output for debugging)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        # include stdout/stderr in the error
        raise RuntimeError(f"Processing failed (rc={proc.returncode}).\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}")

    if not output_p.exists():
        # sometimes MoviePy writes to different name; try to search tmpdir for mp4
        mp4s = list(tmpdir.glob("*.mp4"))
        if mp4s:
            output_p = mp4s[0]
        else:
            raise RuntimeError("Processing completed but no output .mp4 found. Check logs.\nSTDOUT:\n" + proc.stdout)

    return str(output_p)

def cleanup_path(path: str):
    try:
        p = Path(path)
        if p.exists():
            if p.is_file():
                p.unlink()
            else:
                shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass
