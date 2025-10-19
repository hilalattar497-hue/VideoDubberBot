import os
import sys
import tempfile
import shutil
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from gtts import gTTS
import speech_recognition as sr
from googletrans import Translator
import pytesseract
from PIL import Image
from langdetect import detect, DetectorFactory

# =========================
# ✅ Initialization
# =========================
DetectorFactory.seed = 0
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"  # Auto path for Render/Linux

# =========================
# ⚙️ Config Defaults
# =========================
OCR_ENABLED = True
FRAME_OCR_INTERVAL = 1.0
TEXT_CONFIDENCE_THRESHOLD = 55

# Font for Arabic text (Render uses open fonts)
ARABIC_FONT_PATH = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"

# Try linking Tesseract if available
for possible_path in ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]:
    if os.path.exists(possible_path):
        pytesseract.pytesseract.tesseract_cmd = possible_path
        break


# =========================
# 🧠 Helper Functions
# =========================
def try_transcribe_with_languages(audio_file, langs=("fa-IR", "ar-SA", "en-US")):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    for lang in langs:
        try:
            print(f"🎙 Trying recognition with language: {lang}")
            text = r.recognize_google(audio, language=lang)
            print(f"✅ Recognized ({lang}):", text[:80])
            return text, lang
        except Exception as e:
            print(f"❌ Failed {lang}: {e}")
    return None, None


def translate_text(text, dest):
    translator = Translator()
    try:
        if not text.strip():
            return text
        out = translator.translate(text, dest=dest)
        return out.text
    except Exception as e:
        print("⚠️ Translation failed:", e)
        return text


def synthesize_tts(text, lang, out_path):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(out_path)
    except Exception as e:
        print("❌ TTS synthesis failed:", e)


def safe_detect_language(text):
    try:
        if not text.strip():
            return "en"
        return detect(text)
    except Exception:
        return "en"


def get_available_font():
    if os.path.exists(ARABIC_FONT_PATH):
        return ARABIC_FONT_PATH
    return "DejaVuSans.ttf"


# =========================
# 🧾 OCR Functions
# =========================
def extract_ocr_texts(video_path, interval_s=1.0):
    if not OCR_ENABLED:
        return []

    print("🧾 Starting OCR frame extraction...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Could not open video for OCR.")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    results, seen_texts = [], {}
    t = 0.0

    while t < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        try:
            data = pytesseract.image_to_data(pil, output_type=pytesseract.Output.DICT)
        except Exception as e:
            print("⚠️ OCR error at", t, ":", e)
            break

        for i in range(len(data["level"])):
            conf = int(float(data["conf"][i])) if data["conf"][i] != "-1" else -1
            txt = data["text"][i].strip()
            if txt and conf >= TEXT_CONFIDENCE_THRESHOLD and txt.lower() not in seen_texts:
                results.append({
                    "time": t,
                    "text": txt
                })
                seen_texts[txt.lower()] = True
        t += interval_s

    cap.release()
    print(f"✅ OCR found {len(results)} text regions.")
    grouped = [{"start": r["time"], "end": r["time"] + 3.0, "text": r["text"]} for r in results]
    return grouped


def create_ocr_subclips(grouped_texts, target_lang, video_w, video_h):
    clips = []
    font_name = get_available_font()

    for g in grouped_texts:
        start, end = g["start"], g["end"]
        translated_text = translate_text(g["text"], dest=target_lang)
        print(f"🧠 OCR '{g['text']}' → '{translated_text}'")

        try:
            txtclip = (
                TextClip(
                    translated_text,
                    font=font_name,
                    fontsize=int(video_h * 0.06),
                    color="white",
                    stroke_color="black",
                    stroke_width=2,
                    bg_color="rgba(0,0,0,0.4)",
                    method="caption",
                    align="center",
                    size=(int(video_w * 0.9), None)
                )
                .set_start(start)
                .set_end(end)
                .set_position(("center", video_h - int(video_h * 0.2)))
            )
            clips.append(txtclip)
        except Exception as e:
            print(f"⚠️ Subtitle overlay failed: {e}")

    return clips


# =========================
# 🎬 Main Logic
# =========================
def main():
    if len(sys.argv) < 4:
        print("Usage: python video_dubber_plus.py <input_video> <output_video> <lang>")
        sys.exit(1)

    INPUT_VIDEO = sys.argv[1]
    OUTPUT_VIDEO = sys.argv[2]
    target_lang = sys.argv[3]

    print(f"\n🎬 Starting dubbing for: {INPUT_VIDEO} → {OUTPUT_VIDEO} ({target_lang})")

    tmpdir = tempfile.mkdtemp(prefix="vdub_")
    audio_path = os.path.join(tmpdir, "temp_audio.wav")
    dubbed_mp3 = os.path.join(tmpdir, "dubbed_audio.mp3")

    try:
        video = VideoFileClip(INPUT_VIDEO)
        print("🎞 Extracting audio...")
        video.audio.write_audiofile(audio_path, logger=None)

        print("\n🗣 Detecting and transcribing speech...")
        transcribed, detected_lang = try_transcribe_with_languages(audio_path)
        if not transcribed:
            print("❌ No speech recognized.")
            sys.exit(1)

        print(f"✅ Detected language: {detected_lang}")
        print("💬 Translating speech...")
        translated_speech = translate_text(transcribed, dest=target_lang)
        print("🗣 Sample translated:", translated_speech[:100])

        print("🔊 Generating dubbed audio...")
        synthesize_tts(translated_speech, target_lang, dubbed_mp3)

        ocr_groups = extract_ocr_texts(INPUT_VIDEO, FRAME_OCR_INTERVAL) if OCR_ENABLED else []
        print(f"📜 Found {len(ocr_groups)} subtitle entries.")

        dubbed_audio = AudioFileClip(dubbed_mp3)
        base = video.set_audio(dubbed_audio)
        overlays = create_ocr_subclips(ocr_groups, target_lang, video.w, video.h) if ocr_groups else []
        final = CompositeVideoClip([base] + overlays) if overlays else base

        print("🎥 Rendering final video...")
        final.write_videofile(OUTPUT_VIDEO, codec="libx264", audio_codec="aac", logger=None)
        print(f"✅ Done! Dubbed video saved as: {OUTPUT_VIDEO}")

    except Exception as e:
        print("❌ Error:", e)
        sys.exit(1)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
