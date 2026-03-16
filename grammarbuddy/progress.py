"""Progress tracking och statistik."""

import json
import os
from datetime import datetime


DATA_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "grammarbuddy")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_progress() -> dict:
    """Ladda användarens framsteg."""
    _ensure_dir()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_progress()


def save_progress(data: dict):
    """Spara användarens framsteg."""
    _ensure_dir()
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _default_progress() -> dict:
    return {
        "total_exercises": 0,
        "correct_answers": 0,
        "total_analyses": 0,
        "average_score": 0,
        "streak": 0,
        "best_streak": 0,
        "history": [],
        "by_mode": {
            "spelling": {"total": 0, "correct": 0},
            "sentence": {"total": 0, "correct": 0},
            "tense": {"total": 0, "correct": 0},
            "word_order": {"total": 0, "correct": 0},
            "free": {"total": 0, "correct": 0},
        },
        "by_difficulty": {str(i): {"total": 0, "correct": 0} for i in range(5)},
    }


def record_exercise(progress: dict, mode: str, difficulty: int, correct: bool):
    """Registrera en genomförd övning."""
    progress["total_exercises"] += 1
    if correct:
        progress["correct_answers"] += 1
        progress["streak"] += 1
        progress["best_streak"] = max(progress["best_streak"], progress["streak"])
    else:
        progress["streak"] = 0

    if mode in progress["by_mode"]:
        progress["by_mode"][mode]["total"] += 1
        if correct:
            progress["by_mode"][mode]["correct"] += 1

    diff_key = str(difficulty)
    if diff_key in progress["by_difficulty"]:
        progress["by_difficulty"][diff_key]["total"] += 1
        if correct:
            progress["by_difficulty"][diff_key]["correct"] += 1

    progress["history"].append({
        "date": datetime.now().isoformat(),
        "mode": mode,
        "difficulty": difficulty,
        "correct": correct,
    })
    # Keep only last 100 entries
    progress["history"] = progress["history"][-100:]

    save_progress(progress)


def record_analysis(progress: dict, score: int):
    """Registrera en textanalys."""
    progress["total_analyses"] += 1
    n = progress["total_analyses"]
    old_avg = progress["average_score"]
    progress["average_score"] = old_avg + (score - old_avg) / n
    save_progress(progress)


def get_accuracy(progress: dict) -> float:
    """Beräkna total träffsäkerhet i procent."""
    if progress["total_exercises"] == 0:
        return 0.0
    return (progress["correct_answers"] / progress["total_exercises"]) * 100


def load_settings() -> dict:
    """Ladda inställningar."""
    _ensure_dir()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_settings()


def save_settings(data: dict):
    """Spara inställningar."""
    _ensure_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _default_settings() -> dict:
    return {
        "difficulty": 0,
        "mode": "free",
        "language": "sv",
        "use_ai": False,
        "font_size": 14,
    }
