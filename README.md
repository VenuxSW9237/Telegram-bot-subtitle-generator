# 🎬 Telegram Subtitle Bot

Generates English `.srt` subtitle files from videos in **any language** (Hindi, Tamil, Arabic, Chinese, and 90+ more) using OpenAI Whisper.

---

## ✅ Features
- Auto-detects video language — no manual selection needed
- Translates everything to English
- Accepts videos sent natively or as uncompressed documents
- Supports `.mp4`, `.mkv`, `.avi`, `.mov`, and more

---

## 🚀 Deployment on Choreo

### Step 1 — Create a Telegram Bot
1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy your **bot token** (looks like `123456:ABCdef...`)

### Step 2 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/telegram-subtitle-bot.git
git push -u origin main
```

### Step 3 — Create a Choreo Component
1. Go to [console.choreo.dev](https://console.choreo.dev) and sign in
2. Click **Create Component** → **Service**
3. Connect your GitHub repo
4. Set **Build type** to `Dockerfile`
5. Click **Create**

### Step 4 — Add Environment Variable (Secret)
1. In your component, go to **Deploy** → **Configs & Secrets**
2. Click **+ Secret**
3. Add:
   - **Key:** `TELEGRAM_TOKEN`
   - **Value:** your bot token from Step 1
4. Save and redeploy

### Step 5 — Deploy
1. Go to **Build & Deploy**
2. Click **Build** → then **Deploy**
3. Wait for it to go green ✅

Your bot is now live! Open Telegram and send `/start` to your bot.

---

## ⚙️ Configuration

| Environment Variable | Default | Options |
|---|---|---|
| `TELEGRAM_TOKEN` | *(required)* | Your bot token |
| `WHISPER_MODEL` | `base` | `tiny`, `base`, `small`, `medium` |

> **Model trade-off:** `base` is the best balance of speed and accuracy for cloud use. Use `small` or `medium` for more accurate transcription of difficult audio (needs more RAM/CPU).

---

## 📱 How to Use the Bot

| Action | What to do |
|---|---|
| Send video (≤ 20 MB) | Just send it as a video in chat |
| Send larger files | Use 📎 → **File** to send uncompressed |
| Get subtitles | Bot replies with `.srt` file |
| Use subtitles | Open in VLC, MPC-HC, or any player that supports `.srt` |

---

## 🌍 Supported Languages (Sample)
Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Gujarati, Punjabi,
Arabic, Chinese, Japanese, Korean, Spanish, French, German, Portuguese, Russian,
Turkish, Indonesian, Vietnamese, Thai, and 80+ more.

---

## 🛠 Local Development

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install ffmpeg git

# Install Python dependencies
pip install -r requirements.txt

# Run the bot
TELEGRAM_TOKEN=your_token_here python bot.py
```
