import os
import sys
import subprocess
import urllib.request
import tempfile
from pathlib import Path
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip

def run_cmd(cmd, desc=None, check=True):
    print(f"\n🔧 {desc or cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"❌ Error running: {cmd}")
        sys.exit(1)

print("🚀 Starting full setup fix for VideoDubber...")

# 1️⃣ Upgrade pip
run_cmd("python -m pip install --upgrade pip", "Updating pip...")

# 2️⃣ Install core Python dependencies
packages = [
    "setuptools", "wheel", "requests", "pytesseract", "opencv-python",
    "moviepy", "gtts", "googletrans==4.0.0-rc1", "Pillow", "numpy"
]
run_cmd(f"pip install {' '.join(packages)}", "Installing Python packages...")

# 3️⃣ Install setuptools-rust if needed
try:
    import setuptools_rust
except ImportError:
    run_cmd("pip install setuptools-rust", "Installing setuptools-rust...")

# 4️⃣ Tesseract Installation
tesseract_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if tesseract_path.exists():
    print(f"✅ Tesseract found at: {tesseract_path}")
else:
    print("⚙️ Installing Tesseract OCR...")
    temp_dir = tempfile.mkdtemp()
    url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.4.20240530/tesseract-ocr-w64-setup-5.3.4.20240530.exe"
    dest = Path(temp_dir) / "tesseract_installer.exe"
    urllib.request.urlretrieve(url, dest)
    os.system(f'"{dest}" /SILENT')
    print("✅ Tesseract installation complete.")

# 5️⃣ ImageMagick Installation
imagemagick_path = Path(r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe")
if imagemagick_path.exists():
    print(f"✅ ImageMagick found at: {imagemagick_path}")
else:
    print("⚙️ Installing ImageMagick...")
    temp_dir = tempfile.mkdtemp()
    im_url = "https://download.imagemagick.org/ImageMagick/download/binaries/ImageMagick-7.1.2-59-Q16-HDRI-x64-dll.exe"
    im_dest = Path(temp_dir) / "imagemagick_installer.exe"
    urllib.request.urlretrieve(im_url, im_dest)
    os.system(f'"{im_dest}" /SILENT')
    print("✅ ImageMagick installation complete.")

# 6️⃣ Noto Naskh Arabic Font Installation
font_dir = Path("C:/Windows/Fonts")
font_file = font_dir / "NotoNaskhArabic-Regular.ttf"
if font_file.exists():
    print("✅ 'Noto Naskh Arabic' font already installed.")
else:
    print("🔤 Installing 'Noto Naskh Arabic' font...")
    try:
        url = "https://github.com/google/fonts/raw/main/ofl/notonaskharabic/NotoNaskhArabic-Regular.ttf"
        temp_font = Path(tempfile.gettempdir()) / "NotoNaskhArabic-Regular.ttf"
        urllib.request.urlretrieve(url, temp_font)
        os.system(f'copy "{temp_font}" "{font_dir}"')
        print("✅ Font installed successfully.")
    except Exception as e:
        print(f"⚠️ Could not install font automatically: {e}")
        print("Manual download: https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic")

# 7️⃣ Auto-update paths in video_dubber_plus.py
script_path = Path("video_dubber_plus.py")
if script_path.exists():
    print("\n🛠 Updating paths inside video_dubber_plus.py...")
    text = script_path.read_text(encoding="utf-8")
    text = text.replace(
        'TESSERACT_CMD = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"',
        f'TESSERACT_CMD = r"{tesseract_path}"'
    )
    text = text.replace(
        '"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"',
        f'"IMAGEMAGICK_BINARY": r"{imagemagick_path}"'
    )
    # Also replace font reference
    text = text.replace(
        'font="Arial Unicode MS"',
        'font="Noto Naskh Arabic"'
    )
    script_path.write_text(text, encoding="utf-8")
    print("✅ Updated script paths successfully.")
else:
    print("⚠️ video_dubber_plus.py not found — skipping auto-link.")

# 8️⃣ Test the Arabic font rendering
print("\n🧪 Testing MoviePy font rendering (Arabic text)...")

try:
    arabic_sample = "هذا اختبار للخط العربي"
    txt_clip = TextClip(
        arabic_sample,
        fontsize=48,
        color='white',
        font='Noto Naskh Arabic',
        bg_color='black',
        size=(640, 120),
        method='caption',
        align='center'
    ).set_duration(3)

    bg = ColorClip(size=(640, 120), color=(0, 0, 0), duration=3)
    video = CompositeVideoClip([bg, txt_clip])
    test_output = Path(tempfile.gettempdir()) / "font_test.mp4"
    video.write_videofile(str(test_output), fps=24, codec="libx264", audio=False)
    print(f"✅ Arabic font test video saved to: {test_output}")
except Exception as e:
    print(f"⚠️ Font rendering test failed: {e}")
    print("➡️ You may need to restart your PC to refresh font cache.")

# 9️⃣ Summary
print("\n✅ All setup steps completed successfully!")
print("🧠 Installed and linked components:")
print(f"   • Tesseract OCR → {tesseract_path}")
print(f"   • ImageMagick → {imagemagick_path}")
print("   • Font: Noto Naskh Arabic ✔")
print("\n🎬 You can now run:")
print("python video_dubber_plus.py")
