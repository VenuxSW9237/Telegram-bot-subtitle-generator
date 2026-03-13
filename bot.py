import os
import logging
import tempfile
import asyncio
from pathlib import Path

import whisper
import ffmpeg
from telegram import Update, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

# Whisper model size:
#   tiny   ~1 GB VRAM  — fastest,  least accurate
#   base   ~1 GB VRAM  — good balance  ← default
#   small  ~2 GB VRAM  — better accuracy
#   medium ~5 GB VRAM  — great accuracy (slower)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

MAX_FILE_MB = 20          # Telegram Bot API hard limit
AUDIO_FORMAT = "wav"      # whisper works best with wav


# ── Load Whisper once at startup ──────────────────────────────────────────────
logger.info(f"Loading Whisper model: {WHISPER_MODEL} …")
model = whisper.load_model(WHISPER_MODEL)
logger.info("Whisper model loaded ✓")


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_timestamp(seconds: float) -> str:
    """Convert float seconds → SRT timestamp  00:00:00,000"""
    millis = int((seconds % 1) * 1000)
    s = int(seconds)
    h, remainder = divmod(s, 3600)
    m, sec = divmod(remainder, 60)
    return f"{h:02}:{m:02}:{sec:02},{millis:03}"


def segments_to_srt(segments: list) -> str:
    """Convert Whisper segments to SRT string."""
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = format_timestamp(seg["start"])
        end   = format_timestamp(seg["end"])
        text  = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def extract_audio(video_path: str, audio_path: str) -> None:
    """Extract audio from video using ffmpeg."""
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, ac=1, ar="16000", format=AUDIO_FORMAT)
        .overwrite_output()
        .run(quiet=True)
    )


async def process_video(file_path: str) -> str:
    """Run extraction + Whisper transcription in a thread (blocking ops)."""

    def _run():
        with tempfile.NamedTemporaryFile(suffix=f".{AUDIO_FORMAT}", delete=False) as af:
            audio_path = af.name

        try:
            extract_audio(file_path, audio_path)
            result = model.transcribe(
                audio_path,
                task="translate",   # ← always output English
                verbose=False,
            )
            return segments_to_srt(result["segments"])
        finally:
            Path(audio_path).unlink(missing_ok=True)

    return await asyncio.get_event_loop().run_in_executor(None, _run)


async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shared handler for video / document messages."""
    message: Message = update.message

    # Determine the correct Telegram file object
    tg_file_obj = message.video or message.document

    if tg_file_obj is None:
        await message.reply_text("⚠️ Please send a video file.")
        return

    # Check file size
    file_size_mb = (tg_file_obj.file_size or 0) / (1024 * 1024)
    if file_size_mb > MAX_FILE_MB:
        await message.reply_text(
            f"⚠️ File is {file_size_mb:.1f} MB. Telegram limits bot downloads to "
            f"{MAX_FILE_MB} MB.\n\nTip: Compress the video first or trim it into shorter clips."
        )
        return

    status_msg = await message.reply_text(
        "⏳ Downloading your video…"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input_video")

        try:
            # Download
            tg_file = await tg_file_obj.get_file()
            await tg_file.download_to_drive(video_path)

            await status_msg.edit_text("🎙️ Extracting audio & transcribing… (this may take a minute)")

            # Transcribe + translate
            srt_content = await process_video(video_path)

            if not srt_content.strip():
                await status_msg.edit_text("❌ No speech detected in the video. Please try another file.")
                return

            # Save SRT
            srt_path = os.path.join(tmpdir, "subtitles.srt")
            Path(srt_path).write_text(srt_content, encoding="utf-8")

            await status_msg.delete()
            await message.reply_document(
                document=open(srt_path, "rb"),
                filename="subtitles.srt",
                caption="✅ *Subtitles ready!* (Translated to English)\n\nOpen with VLC, MPC-HC, or drag onto your video player.",
                parse_mode="Markdown",
            )

        except ffmpeg.Error as e:
            logger.exception("FFmpeg error")
            await status_msg.edit_text(
                "❌ Could not process this video format. Try converting it to MP4 first."
            )
        except Exception as e:
            logger.exception("Unexpected error")
            await status_msg.edit_text(f"❌ Something went wrong: {e}")


# ── Command Handlers ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *Welcome to SubtitleBot!*\n\n"
        "Send me any video and I'll generate English subtitles for it — "
        "no matter what language it's in.\n\n"
        "📌 *How to use:*\n"
        "• Send a video directly (up to 20 MB)\n"
        "• Or send as a *File/Document* to avoid compression\n\n"
        "🌍 Supports 99+ languages including Hindi, Tamil, Telugu, Arabic, Chinese, and more.",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *Help*\n\n"
        "*Commands:*\n"
        "/start — Welcome message\n"
        "/help  — This message\n\n"
        "*Sending videos:*\n"
        "• Just send the video in the chat\n"
        "• For files > Telegram compression, use 📎 → *File* option\n\n"
        "*Output:*\n"
        "You'll receive an `.srt` subtitle file translated to English.\n\n"
        "*Supported languages:* Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, "
        "Arabic, Chinese, Japanese, Spanish, French, German, and 80+ more.",
        parse_mode="Markdown",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Handle videos sent as native video
    app.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    # Handle videos sent as documents (uncompressed)
    app.add_handler(MessageHandler(filters.Document.VIDEO, handle_video_file))

    logger.info("Bot is running…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
