# 🤖 AI Voice Receptionist

> **An open-source, self-hosted AI phone receptionist that answers calls, understands spoken requests, and books appointments — powered by Python, spaCy, and gTTS, with an Android client.**

---

## 📸 What It Does

AI Voice Receptionist acts as a 24/7 virtual front desk for any business. It connects to an Android phone, listens to callers in real-time, understands their intent (book / cancel / reschedule / enquire), and responds in a natural spoken voice — all while updating a live web dashboard.

**Key capabilities:**
- 🎙️ Real-time voice streaming over WebSocket (16 kHz PCM)
- 🧠 Intent + entity extraction (spaCy NLP): service, date, time, caller name
- 📅 Smart appointment booking with one-question-at-a-time prompting
- ✅ Business hours and service validation using a natural-language business profile
- 🔊 Text-to-speech responses (gTTS → MP3 streamed to Android)
- 📊 Live web dashboard: calls, appointments, customers, analytics
- ⚙️ Settings page where you describe your business in plain English — the AI extracts everything automatically

---

## 🏗️ Architecture

```
┌─────────────────────┐        WebSocket (ws://)         ┌──────────────────────┐
│   Android App       │ ◄──────────────────────────────► │   FastAPI Backend     │
│  (Call Screen UI)   │   16kHz PCM audio (binary)       │                       │
│                     │   JSON control messages           │  ┌─────────────────┐  │
│  • Mic capture      │                                   │  │  Whisper STT    │  │
│  • TTS playback     │                                   │  │  spaCy NLU      │  │
│  • Chat bubbles     │                                   │  │  gTTS TTS       │  │
│  • Pulse animation  │                                   │  │  SQLite DB      │  │
└─────────────────────┘                                   │  └─────────────────┘  │
                                                          └──────────────────────┘
                                                                    │
                                                          ┌─────────▼────────────┐
                                                          │   Web Dashboard       │
                                                          │  (Static HTML/JS/CSS) │
                                                          │  /dashboard           │
                                                          │  /settings            │
                                                          └──────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| API Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Real-time | WebSocket via `fastapi`/`starlette` |
| Speech-to-Text | [OpenAI Whisper](https://github.com/openai/whisper) (`base` model) |
| NLU / NLP | [spaCy](https://spacy.io/) `en_core_web_sm` + PhraseMatcher |
| Text-to-Speech | [gTTS](https://github.com/pndurette/gTTS) (Google TTS) |
| Database ORM | [SQLAlchemy](https://www.sqlalchemy.org/) with SQLite |
| Business Profile | Custom regex parser (`services/business_profile.py`) |
| Server | [Uvicorn](https://www.uvicorn.org/) ASGI |
| Audio VAD | `audioop.rms` silence detection |

### Android App
| Layer | Technology |
|-------|-----------|
| Language | Java |
| Min SDK | API 26 (Android 8.0) |
| Audio Capture | `AudioRecord` (16 kHz, Mono, PCM 16-bit) |
| Audio Playback | `MediaPlayer` (MP3) |
| WebSocket | [OkHttp](https://square.github.io/okhttp/) |
| UI | ConstraintLayout, custom drawables, programmatic chat bubbles |
| View Binding | Android ViewBinding |

### Frontend Dashboard
| Layer | Technology |
|-------|-----------|
| Framework | Vanilla HTML + CSS + JavaScript |
| Charts | Custom JS renderers |
| Fonts | Google Fonts (Outfit) |
| Served by | FastAPI `StaticFiles` |

---

## 📋 Prerequisites

### Backend
- Python **3.10+** (tested on 3.10.x)
- `pip` or a virtual environment tool
- Internet access (first run downloads Whisper model ~140MB and spaCy model ~12MB)
- **FFmpeg** — required by Whisper for audio decoding
  - Windows: `winget install ffmpeg` or download from https://ffmpeg.org/download.html
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### Android
- Android Studio **Hedgehog** or newer
- Android device or emulator running **API 26+**
- Both device and backend server on the **same Wi-Fi network** (or use ngrok for remote)
- JDK **11 or 17** (required for Gradle 8.x — see Android setup below)

---

## 🚀 Backend Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ai-receptionist.git
cd ai-receptionist
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv .venv310
.venv310\Scripts\activate

# macOS / Linux
python3 -m venv .venv310
source .venv310/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download the spaCy language model
```bash
python -m spacy download en_core_web_sm
```

### 5. Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server binds to **all network interfaces** (`0.0.0.0`) so your Android device can connect over Wi-Fi.

### 6. Open the dashboard
Visit **http://127.0.0.1:8000** in your browser → redirects to `/dashboard`.

---

## ⚙️ Configure Your Business (Important!)

Before the AI can answer intelligently, tell it about your business:

1. Go to **http://127.0.0.1:8000/settings**
2. In the **Business Profile** textarea, write a natural description:
   ```
   We are a hair salon called Style & Co. We offer haircuts, beard trims, 
   shaves, fades, hair coloring and hair treatments. We are open Monday to 
   Saturday from 9 AM to 7 PM. We are located in Pune, Maharashtra.
   ```
3. Click **"Preview parsed profile"** — verify the AI extracted the right name, services, and hours
4. Click **"Save changes"**

The AI now uses this profile to:
- Greet callers: *"Thank you for calling Style & Co!"*
- Validate services: *"We offer haircuts, beard trims... which would you like?"*
- Enforce hours: *"We're open until 7 PM, would you like a time within those hours?"*
- Answer enquiries: *"We offer haircuts, beard trims... open Monday to Saturday 9 AM to 7 PM"*

---

## 📱 Android App Setup

### Fix JDK Version (required)
The Android Gradle plugin 8.2.2 requires **JDK 11+**. If you see Java version errors:

1. Download [JDK 17](https://www.oracle.com/java/technologies/downloads/#java17) or use `winget install Microsoft.OpenJDK.17`
2. In Android Studio: **File → Project Structure → SDK Location → Gradle JDK** → select JDK 17
3. Or set environment variable: `JAVA_HOME=C:\Program Files\Microsoft\jdk-17...`

### Build the app
1. Open Android Studio
2. **File → Open** → select `android-app/` folder
3. Wait for Gradle sync to complete
4. **Build → Make Project**

### Connect to your backend

**Find your computer's local IP address:**
```bash
# Windows
ipconfig
# Look for "IPv4 Address" under your Wi-Fi adapter, e.g. 192.168.1.8

# macOS / Linux
ifconfig | grep "inet "
```

**Set the server URL in the app:**
1. Run the app on your device
2. Tap the ⚙️ **Settings** icon (top-left)
3. Set **Server WebSocket URL** to:
   ```
   ws://192.168.1.8:8000/ws/audio
   ```
   Replace `192.168.1.8` with your actual local IP.
4. Save

> 💡 **Tip**: Make sure your phone and computer are on the **same Wi-Fi network**. The default URL in the app uses `10.0.2.2` (Android emulator loopback to host) — change it for a physical device.

### Deploy to physical device
1. Enable **Developer Options** on your Android phone:
   - Settings → About Phone → tap **Build Number** 7 times
2. Enable **USB Debugging** in Developer Options
3. Connect via USB → Android Studio should detect the device
4. Click ▶ **Run** to install and launch

---

## 📞 How a Call Works (End-to-End)

```
1. User taps green call button on Android
2. App connects WebSocket to ws://<server>/ws/audio
3. Server loads business profile from DB
4. Server sends greeting TTS: "Thank you for calling Style & Co..."
5. Android plays MP3 greeting through speaker
6. Android streams 16kHz PCM microphone audio to server
7. Server VAD detects end of speech (silence > 1.5s)
8. Whisper transcribes the audio chunk
9. spaCy extracts: intent + service + date + time + name
10. Reception logic validates against business profile
    → If info missing: asks one clarifying question
    → If service invalid: lists valid services
    → If outside hours: tells caller business hours
    → If all info present: creates appointment in DB
11. Response text converted to MP3 via gTTS
12. MP3 streamed back to Android over WebSocket (binary frames)
13. Android plays response, then resumes listening
14. Dashboard auto-refreshes showing new call + appointment
```

---

## 🗂️ Project Structure

```
ai-receptionist/
├── app/
│   └── main.py                  # FastAPI app entry point
├── db/
│   └── session.py               # SQLAlchemy session + DB init
├── models/
│   ├── appointment.py           # Appointment ORM model
│   ├── call.py                  # Call log ORM model
│   ├── customer.py              # Customer ORM model
│   └── setting.py               # Settings key-value ORM model
├── routes/
│   ├── appointments.py          # CRUD API for appointments
│   ├── calls.py                 # Call history API
│   ├── customers.py             # Customer API
│   ├── dashboard.py             # Dashboard data aggregation
│   ├── settings.py              # Settings API + /parse-profile
│   ├── tts.py                   # TTS test endpoint
│   └── websocket.py             # Main WebSocket handler (call flow)
├── services/
│   ├── business_profile.py      # Free-text business description parser
│   ├── nlu.py                   # Intent + entity extraction (spaCy)
│   ├── reception.py             # Booking/cancel/reschedule logic
│   ├── stt.py                   # Whisper speech-to-text
│   └── tts.py                   # gTTS text-to-speech
├── static/
│   ├── dashboard.html           # Web dashboard UI
│   ├── dashboard.css            # Dashboard styles
│   ├── dashboard.js             # Dashboard logic
│   └── settings.html            # Business settings UI
├── android-app/
│   └── app/src/main/
│       ├── java/com/aireceptionist/app/
│       │   ├── MainActivity.java        # Call screen + WebSocket client
│       │   └── SettingsActivity.java    # Server URL settings
│       └── res/
│           ├── layout/activity_main.xml # Call screen layout
│           └── drawable/               # Custom shapes + buttons
└── requirements.txt
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/ws/audio` | Main call WebSocket (binary PCM in, JSON+binary out) |
| `GET` | `/dashboard` | Dashboard HTML |
| `GET` | `/dashboard/data` | Dashboard JSON data |
| `GET` | `/api/settings` | Get all settings |
| `PUT` | `/api/settings/{key}` | Update a setting |
| `POST` | `/api/settings/parse-profile` | Preview parsed business profile |
| `GET` | `/api/appointments` | List appointments |
| `POST` | `/api/appointments` | Create appointment |
| `GET` | `/api/calls` | List call logs |
| `GET` | `/api/customers` | List customers |
| `GET` | `/health` | Health check |

### WebSocket Message Protocol

**Server → Client (JSON):**
```json
{ "type": "action_result", "success": true, "message": "Thank you for calling..." }
{ "type": "transcript", "text": "I'd like a haircut tomorrow at 3pm", "call_id": 42 }
{ "type": "nlu_result", "intent": "book", "entities": {"service": "haircut", "date": "tomorrow", "time": "3pm", "name": "Rahul"} }
{ "type": "tts_start" }
// ... binary MP3 frames ...
{ "type": "tts_end" }
{ "type": "error", "message": "..." }
```

**Client → Server:**
- Binary frames: raw 16-bit PCM audio at 16 kHz
- Text: `{"type": "end_of_utterance"}` (optional manual trigger)

---

## 🩹 Troubleshooting

### "Connection failed" on Android
- Ensure phone and computer are on **same Wi-Fi network**
- Check your computer's IP with `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- Ensure the server is running with `--host 0.0.0.0`
- Try `ws://YOUR_IP:8000/ws/audio` in the app settings

### Whisper not transcribing
- Ensure FFmpeg is installed: `ffmpeg -version`
- The first run downloads the Whisper `base` model (~140MB) — wait for it
- Check server terminal for errors

### "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### Android Gradle build fails (Java version)
- Use JDK 11 or 17 (not JDK 8 or 21+)
- In Android Studio: File → Project Structure → Gradle JDK → JDK 17

### Business profile not working
- Go to `/settings`, re-enter your description, click **Preview** to verify extraction
- Include explicit keywords: *"we offer"*, *"open Monday to Saturday"*, *"called [Name]"*

### Dashboard shows no data
- Make at least one call through the Android app first
- Refresh the dashboard (auto-refreshes every 60 seconds)

---

## 🤝 Contributing

1. Fork the repo
2. Create your branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) — speech recognition
- [spaCy](https://spacy.io/) — NLP / intent extraction
- [gTTS](https://github.com/pndurette/gTTS) — text-to-speech
- [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework
- [OkHttp](https://square.github.io/okhttp/) — Android WebSocket client
