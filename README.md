# MS RehaGame

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pygame-2.x-green?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/MediaPipe-local-orange?logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-embedded-lightblue?logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow"/>
</p>

> **A camera-based serious game for upper limb and cognitive rehabilitation of Multiple Sclerosis patients — no special hardware required.**

---

## Table of Contents

- [Overview](#overview)
- [Games](#games)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Game](#running-the-game)
- [How Hand Tracking Works](#how-hand-tracking-works)
- [Cognitive Modes](#cognitive-modes)
- [HUD Controls](#hud-controls)
- [Statistics & Export](#statistics--export)
- [Database Schema](#database-schema)
- [Clinical Background](#clinical-background)
- [Team](#team)

---

## Overview

Multiple Sclerosis (MS) affects ~2.9 million people worldwide. It progressively impairs fine motor control of the hands and cognitive abilities including memory, attention, and processing speed. Traditional rehabilitation exercises are clinically effective but monotonous, leading to low adherence.

**MS RehaGame** is a serious game designed to make rehabilitation enjoyable while remaining clinically grounded. It targets:

- **Fine motor skills** — thumb opposition and precision pinch exercises, mirroring standard occupational therapy tasks.
- **Cognitive training** — memory, attention, and reaction speed through game-mode variations.
- **Long-term adherence** — progress tracking, achievements, and clinical export tools for therapists.

The project is inspired by and extends the research of **Kecman, B. (2024) — *Analysis, Design and Implementation of a Serious Game for Upper Limb and Cognitive Training Using Leap Motion for MS Patients*, TU Wien**. Unlike the reference, we use a standard webcam + MediaPipe for hand tracking (no dedicated hardware needed), and Python + Pygame instead of Unity.

---

## Games

### 🎮 Thumb Tango — Opposition Challenge

> Trains: thumb-to-finger opposition | Inspired by: turning a key, picking up small objects

Colored balls fall down the screen and reach a split zone. The player must touch their thumb to the correct finger to route the ball into the matching-color lane.

| Finger | Lane | Color |
|--------|------|-------|
| Index  | 1    | Red   |
| Middle | 2    | Green |
| Ring   | 3    | Blue  |
| Little | 4    | Yellow |

**Scoring:** +100 correct, -30 miss, +500 streak bonus (×10), +10,000 perfect game.

---

### 🎮 Mindful Tower — Pinch Perfect

> Trains: precision pinch and drag | Inspired by: picking up coins, placing pegs

A target color pattern is shown. The player pinches blocks from the source tray and drags them to matching markers in the build area.

| Level | Blocks | Block Size | Snap Distance |
|-------|--------|-----------|---------------|
| 1 — Beginner     | 4  (2×2) | 60 px | 50 px |
| 2 — Intermediate | 8  (2×4) | 45 px | 35 px |
| 3 — Advanced     | 16 (4×4) | 30 px | 20 px |

---

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Language | Python 3.11+ | Core runtime |
| Game Engine | Pygame 2.x | Window, rendering, event loop, 60 FPS |
| Hand Tracking | MediaPipe (local) | Webcam-based hand landmark detection — no API, no internet |
| Video Input | OpenCV (cv2) | Webcam frame capture and preprocessing |
| Database | SQLite3 (stdlib) | Embedded local database for all user data |
| Data Analysis | Pandas | Session statistics, weekly progress aggregation |
| Export | OpenPyXL | Clinical Excel report generation |
| Charts | Matplotlib | Statistics screen graphs embedded as Pygame surfaces |
| Auth | bcrypt | Secure password hashing |
| Concurrency | threading (stdlib) | MediaPipe runs on a background thread |

> 💡 **No external API calls are made during gameplay.** MediaPipe runs 100% on-device.

---

## Project Structure

```
ms_rehab_game/
├── main.py                    # Entry point — ScreenManager, game loop
├── settings.py                # Colors, constants, game configs
├── database.py                # All SQLite operations + Excel export
├── gesture_detector.py        # MediaPipe background thread, GestureSnapshot
│
├── games/
│   ├── base_game.py           # Shared HUD, pause/confirm dialog, hand cursor
│   ├── thumb_tango.py         # Game 1: Thumb opposition falling balls
│   └── mindful_tower.py       # Game 2: Pinch drag-and-drop tower
│
├── screens/
│   ├── base.py
│   ├── login_screen.py
│   ├── start_screen.py
│   ├── game_menu_screen.py
│   ├── level_select_screen.py
│   ├── tutorial_screen.py
│   ├── statistics_screen.py
│   └── settings_screen.py
│
├── ui/
│   └── components.py          # Button, draw_text, draw_progress_bar, etc.
│
├── assets/
│   ├── sounds/                # .wav sound effects
│   ├── fonts/                 # UI fonts
│   └── models/                # hand_landmarker.task (auto-downloaded)
│
└── data/
    └── game.db                # SQLite database (auto-created on first launch)

exports/                       # Excel reports saved here on export
```

---

## Installation

### Requirements

- Python 3.11 or higher
- A webcam

### Steps

```bash
# Clone the repository
git clone https://github.com/your-team/ms_rehab_game.git
cd ms_rehab_game

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / macOS

# Install dependencies
pip install pygame mediapipe opencv-python pandas openpyxl matplotlib bcrypt

# Launch the game
python launch_game.py
```

The database and asset directories are created automatically on first launch. The MediaPipe hand landmarker model is downloaded once on first run.

---

## Running the Game

```bash
python launch_game.py
```

1. **Login** — Create an account or log in with existing credentials.
2. **Choose a game** — Thumb Tango or Mindful Tower.
3. **Configure** — Set your controller hand, session duration, cognitive mode, and sound preferences.
4. **Select difficulty** — Level 1 (Beginner), 2 (Intermediate), or 3 (Advanced).
5. **Play** — Use your webcam and hand gestures to interact.
6. **Review** — View your session statistics and export a clinical report.

---

## How Hand Tracking Works

MS RehaGame uses **Google MediaPipe** for real-time hand landmark detection. The entire pipeline runs locally on your device:

```
Webcam → OpenCV frame → MediaPipe → 21 landmarks (x,y,z) → Gesture logic → GestureSnapshot
```

### Key Gestures

| Gesture | Detection Method | Used For |
|---------|-----------------|----------|
| **Pinch** | Distance between landmark 4 (thumb tip) and landmark 8 (index tip) < 40 px | Pick up blocks, click HUD buttons |
| **Thumb Opposition** | Thumb tip within 40 px of any fingertip | Route balls in Thumb Tango |
| **Drag** | Hold pinch while moving hand | Move blocks in Mindful Tower |
| **Both-hands open** | Hold both palms open for 0.4s | Pause in Mindful Tower |
| **Hint gesture** | Extend non-controlling hand | Reveal target pattern in Memory mode |

The gesture thread updates at ~100 Hz. The main game thread reads one snapshot per frame (60 FPS) without blocking.

---

## Cognitive Modes

### Thumb Tango
| Mode | Description |
|------|------------|
| **Calm** | Lane colors are fixed. Purely physical challenge. |
| **Shuffle Lanes** | Lane colors reshuffle randomly every 10 seconds. |
| **Color Reveal** | Ball color hidden until it enters the split zone. |
| **Memory** | Ball color shown briefly, then hidden. |

### Mindful Tower
| Mode | Description |
|------|------------|
| **Pinch Precision** | Target pattern always visible. |
| **Memory** | Target hidden after countdown. Second-hand gesture reveals it briefly. |

---

## HUD Controls

Every game session has three buttons in the top-right corner:

| Button | Color | Action |
|--------|-------|--------|
| **PAUSE** | Cyan | Pauses the game. Timer freezes. |
| **EXIT** | Red | Confirms exit to main menu. |
| **RESET** | Orange | Confirms game reset. |

All buttons work via **mouse click** or **hand pinch gesture** (hover hand over button, then pinch to activate).

Confirmation dialogs ("Are you sure?") freeze the timer and require explicit YES/NO input before acting.

---

## Statistics & Export

The Statistics screen provides:

- Total sessions, best score, average accuracy, total training time
- Medal breakdown (Bronze → Silver → Gold → Platinum)
- Session score and accuracy charts over time (Matplotlib)
- Per-game achievement gallery

### Clinical Export

Click **Export Report** to generate an Excel file at:

```
exports/{username}_sessions.xlsx
```

The file contains 3 worksheets:

| Sheet | Contents |
|-------|---------|
| Clinical Summary | Totals, bests, averages, medals |
| Weekly Progress | Avg score + accuracy per calendar week |
| Session Log | Full record of every session with all metrics |

---

## Database Schema

SQLite database at `ms_rehab_game/data/game.db`:

```sql
users           (id, username, hashed_password, created_at)
game_sessions   (id, user_id, game_name, level, cognitive_mode, score, 
                 accuracy, duration_seconds, correct_actions, total_actions, 
                 hand, played_at)
achievements    (id, user_id, game_name, achievement_key, unlocked_at)
paused_sessions (id, user_id, game_name, time_remaining, state_json, paused_at)
user_game_settings (id, user_id, game_name, settings_json)
```

---

## Clinical Background

This project is grounded in the following clinical evidence:

- **66%** of MS patients experience upper limb motor dysfunction (Spooren et al., 2012).
- **50–60%** experience cognitive impairments including memory and attention deficits (ÖMSB, 2020).
- **Neuroplasticity**: repetitive exercises restructure neural pathways, improving motor control.
- **Serious games** increase therapy adherence by making repetitive exercises enjoyable (Kecman, 2024; Baranyi et al., 2023).
- The reference prototype (Unity + Leap Motion) achieved **SUS = 84.5** (Good) and **GEQ positive affect = 3.26/4** in evaluation with MS patients and volunteers.

### Design Principles from Clinical Consultation

| Principle | Implementation |
|-----------|---------------|
| Short sessions (fatigue management) | Configurable 3/5/10 min duration |
| High contrast UI (optic neuritis) | Dark background, pure color game objects |
| No punishment for mistakes | -30 pts miss vs +100 pts correct; no negative total |
| Hint system (memory impairment) | Second-hand gesture reveals target |
| Progress tracking for therapists | Excel export with Clinical Summary sheet |
| Home-use without therapist | Full tutorial + gesture preview on every launch |

---

## Team

Developed as a biomedical engineering competition project focused on serious games for Parkinson's/tremor rehabilitation, adapted for Multiple Sclerosis.

- Built with Python, Pygame, MediaPipe
- Clinically grounded in peer-reviewed MS rehabilitation research
- Reference: Kecman, B. (2024). *Analysis, Design and Implementation of a Serious Game for Upper Limb and Cognitive Training Using Leap Motion for Multiple Sclerosis Patients*. TU Wien.

---

<p align="center">Made with ❤️ for MS patients and their therapists</p>
