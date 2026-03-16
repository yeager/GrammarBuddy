"""AI-baserad grammatikanalys för svenska."""

import json
import os
import re
from enum import IntEnum


class Difficulty(IntEnum):
    """Svårighetsnivåer för SFI."""
    SFI_A = 0  # Grundläggande
    SFI_B = 1  # Fortsättning
    SFI_C = 2  # Mellannivå
    SFI_D = 3  # Avancerad
    ADVANCED = 4  # Avancerat


DIFFICULTY_LABELS = {
    Difficulty.SFI_A: "SFI A – Grundläggande",
    Difficulty.SFI_B: "SFI B – Fortsättning",
    Difficulty.SFI_C: "SFI C – Mellannivå",
    Difficulty.SFI_D: "SFI D – Avancerad",
    Difficulty.ADVANCED: "Avancerat",
}


class ExerciseMode:
    """Övningslägen."""
    SPELLING = "spelling"
    SENTENCE = "sentence"
    TENSE = "tense"
    WORD_ORDER = "word_order"
    FREE = "free"


MODE_LABELS = {
    ExerciseMode.SPELLING: "Stavning",
    ExerciseMode.SENTENCE: "Meningsbyggnad",
    ExerciseMode.TENSE: "Tempus",
    ExerciseMode.WORD_ORDER: "Ordföljd",
    ExerciseMode.FREE: "Fri skrivning",
}


# Built-in grammar rules for offline analysis
COMMON_ERRORS = {
    "spelling": [
        (r"\bdem\b", "dem/de", "Kontrollera: menar du 'de' (subjekt) eller 'dem' (objekt)?"),
        (r"\bdom\b", "dom→de/dem", "'Dom' är talspråk. Skriv 'de' eller 'dem'."),
        (r"\bmej\b", "mej→mig", "'Mej' är talspråk. Skriv 'mig'."),
        (r"\bdej\b", "dej→dig", "'Dej' är talspråk. Skriv 'dig'."),
        (r"\bsej\b", "sej→sig", "'Sej' är talspråk. Skriv 'sig'."),
        (r"\bnån\b", "nån→någon", "'Nån' är talspråk. Skriv 'någon'."),
        (r"\bnåt\b", "nåt→något", "'Nåt' är talspråk. Skriv 'något'."),
        (r"\bva\b", "va→vad/var", "'Va' är talspråk. Skriv 'vad' eller 'var'."),
    ],
    "word_order": [
        (r"\b(igår|idag|imorgon)\s+(jag|han|hon|vi|de|du)\s+",
         "ordföljd", "I bisatser och efter tidsadverb kommer verbet före subjektet: "
                      "'Igår gick jag' (inte 'Igår jag gick')."),
    ],
    "tense": [
        (r"\b(jag|han|hon|vi|de|du)\s+(ska|kommer att)\s+\w+de\b",
         "tempus", "Blanda inte futurum med preteritum. "
                   "'Ska' + infinitiv, inte 'ska' + preteritum."),
    ],
}

# Exercise sentences per difficulty and mode
EXERCISES = {
    Difficulty.SFI_A: {
        ExerciseMode.SPELLING: [
            {"prompt": "Skriv rätt: Jag _____ (ha) en katt.", "answer": "har",
             "hint": "Verbet 'ha' i presens blir 'har'."},
            {"prompt": "Skriv rätt: Hon _____ (vara) glad.", "answer": "är",
             "hint": "Verbet 'vara' i presens blir 'är'."},
            {"prompt": "Skriv rätt: Vi _____ (bo) i Stockholm.", "answer": "bor",
             "hint": "Verbet 'bo' i presens: ta bort -a, lägg till -r."},
        ],
        ExerciseMode.SENTENCE: [
            {"prompt": "Gör en mening: jag / heter / Anna",
             "answer": "Jag heter Anna.", "hint": "Börja med stor bokstav, avsluta med punkt."},
            {"prompt": "Gör en mening: han / bor / i Malmö",
             "answer": "Han bor i Malmö.", "hint": "Subjekt + verb + resten."},
        ],
        ExerciseMode.WORD_ORDER: [
            {"prompt": "Rätt ordning: bor / var / du / ?",
             "answer": "Var bor du?", "hint": "I frågor: frågeord + verb + subjekt."},
        ],
        ExerciseMode.TENSE: [
            {"prompt": "Presens av 'äta': Jag _____ mat.", "answer": "äter",
             "hint": "Grupp 4-verb: äta → äter."},
        ],
    },
    Difficulty.SFI_B: {
        ExerciseMode.SPELLING: [
            {"prompt": "Skriv rätt: De _____ (gå) till skolan igår.", "answer": "gick",
             "hint": "Verbet 'gå' i preteritum (dåtid) blir 'gick'."},
            {"prompt": "Skriv rätt: Barnen _____ (leka) i parken.", "answer": "leker",
             "hint": "Verbet 'leka' i presens: leka → leker."},
        ],
        ExerciseMode.SENTENCE: [
            {"prompt": "Bilda en fråga: du / kan / svenska / tala",
             "answer": "Kan du tala svenska?",
             "hint": "Ja/nej-fråga: verb + subjekt + objekt + ?"},
        ],
        ExerciseMode.WORD_ORDER: [
            {"prompt": "Rätt ordning: igår / jag / till affären / gick",
             "answer": "Igår gick jag till affären.",
             "hint": "Tidsadverb först → omvänd ordföljd (verb före subjekt)."},
        ],
        ExerciseMode.TENSE: [
            {"prompt": "Preteritum av 'arbeta': Hon _____ hela dagen.",
             "answer": "arbetade", "hint": "Grupp 1-verb: arbeta → arbetade."},
        ],
    },
    Difficulty.SFI_C: {
        ExerciseMode.SPELLING: [
            {"prompt": "Skriv rätt: Jag har _____ (skriva) ett brev.", "answer": "skrivit",
             "hint": "Supinum av 'skriva': skrivit."},
        ],
        ExerciseMode.SENTENCE: [
            {"prompt": "Bilda en bisats: Jag vet / han / inte / kommer",
             "answer": "Jag vet att han inte kommer.",
             "hint": "Bisats med 'att': negation före verb i bisats."},
        ],
        ExerciseMode.WORD_ORDER: [
            {"prompt": "Skriv om: Jag gillar inte kaffe → Kaffe ...",
             "answer": "Kaffe gillar jag inte.",
             "hint": "Fronting av objekt → omvänd ordföljd."},
        ],
        ExerciseMode.TENSE: [
            {"prompt": "Perfekt av 'springa': Vi har _____.",
             "answer": "sprungit", "hint": "Grupp 4: springa → sprungit."},
        ],
    },
    Difficulty.SFI_D: {
        ExerciseMode.SPELLING: [
            {"prompt": "Rätt form: Den _____ (röd) bilen är min.", "answer": "röda",
             "hint": "Bestämd form av adjektiv: röd → röda."},
        ],
        ExerciseMode.SENTENCE: [
            {"prompt": "Binda ihop: Han kom sent. Han hade missat bussen.",
             "answer": "Han kom sent eftersom han hade missat bussen.",
             "hint": "Använd 'eftersom' för orsak."},
        ],
        ExerciseMode.WORD_ORDER: [
            {"prompt": "Skriv om med bisats: Han är trött. Han sov dåligt.",
             "answer": "Han är trött eftersom han sov dåligt.",
             "hint": "Bisats: subjunktion + subjekt + verb."},
        ],
        ExerciseMode.TENSE: [
            {"prompt": "Pluskvamperfekt: Innan jag kom hade hon redan _____. (gå)",
             "answer": "gått",
             "hint": "Pluskvamperfekt: hade + supinum. Gå → gått."},
        ],
    },
    Difficulty.ADVANCED: {
        ExerciseMode.SPELLING: [
            {"prompt": "Rätt: Den _____ (erfara) läraren hjälpte oss.", "answer": "erfarna",
             "hint": "Bestämd form av perfektparticip: erfaren → erfarna."},
        ],
        ExerciseMode.SENTENCE: [
            {"prompt": "Skriv om i passiv: Eleverna läste boken.",
             "answer": "Boken lästes av eleverna.",
             "hint": "s-passiv: verb + s. Läste → lästes."},
        ],
        ExerciseMode.WORD_ORDER: [
            {"prompt": "Korrekt: Inte bara ... utan också: lärare / elever / protesterade",
             "answer": "Inte bara lärarna utan också eleverna protesterade.",
             "hint": "Korrelativa konjunktioner: inte bara ... utan också."},
        ],
        ExerciseMode.TENSE: [
            {"prompt": "Konjunktiv: Om jag _____ (vara) rik, skulle jag resa.",
             "answer": "vore", "hint": "Konjunktiv av 'vara': vore."},
        ],
    },
}


class GrammarAnalysis:
    """Result of grammar analysis."""

    def __init__(self, original: str, corrected: str, errors: list, explanation: str,
                 score: int):
        self.original = original
        self.corrected = corrected
        self.errors = errors  # list of (type, description)
        self.explanation = explanation
        self.score = score  # 0-100


class GrammarEngine:
    """Grammatikmotor med inbyggda regler och valfri AI-integration."""

    def __init__(self):
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        self._use_ai = bool(self._api_key)

    @property
    def ai_available(self) -> bool:
        return self._use_ai

    def analyze(self, text: str, difficulty: Difficulty,
                mode: str = ExerciseMode.FREE) -> GrammarAnalysis:
        """Analysera text med inbyggda regler (och AI om tillgängligt)."""
        if not text.strip():
            return GrammarAnalysis(text, text, [], "Skriv en mening att analysera.", 0)

        errors = []
        corrected = text

        # Rule-based analysis
        categories = ["spelling"]
        if mode in (ExerciseMode.WORD_ORDER, ExerciseMode.FREE):
            categories.append("word_order")
        if mode in (ExerciseMode.TENSE, ExerciseMode.FREE):
            categories.append("tense")

        for cat in categories:
            for pattern, err_type, desc in COMMON_ERRORS.get(cat, []):
                if re.search(pattern, text, re.IGNORECASE):
                    errors.append((err_type, desc))

        # Basic checks
        if text and not text[0].isupper():
            errors.append(("stor bokstav", "Meningar börjar med stor bokstav."))
            corrected = corrected[0].upper() + corrected[1:]

        if text.strip() and text.strip()[-1] not in ".!?":
            errors.append(("skiljetecken", "Avsluta meningen med punkt, frågetecken eller utropstecken."))
            corrected = corrected.rstrip() + "."

        # Double spaces
        if "  " in text:
            errors.append(("mellanslag", "Ta bort dubbla mellanslag."))
            corrected = re.sub(r" {2,}", " ", corrected)

        # Score
        if not errors:
            score = 100
        else:
            score = max(0, 100 - len(errors) * 15)

        # Explanation
        if errors:
            parts = ["Jag hittade några saker att förbättra:\n"]
            for i, (etype, desc) in enumerate(errors, 1):
                parts.append(f"{i}. ({etype}) {desc}")
            explanation = "\n".join(parts)
        else:
            explanation = "Bra jobbat! Meningen ser korrekt ut. 👍"

        return GrammarAnalysis(text, corrected, errors, explanation, score)

    def get_exercise(self, difficulty: Difficulty, mode: str) -> dict | None:
        """Hämta en övning baserat på svårighetsgrad och läge."""
        exercises = EXERCISES.get(difficulty, {}).get(mode, [])
        if not exercises:
            return None
        import random
        return random.choice(exercises)

    def check_exercise_answer(self, exercise: dict, answer: str) -> tuple[bool, str]:
        """Kontrollera svar på övning."""
        correct = answer.strip().lower() == exercise["answer"].strip().lower()
        if correct:
            feedback = "Rätt! Bra jobbat! ✓"
        else:
            feedback = (f"Inte riktigt. Rätt svar: {exercise['answer']}\n"
                        f"Tips: {exercise['hint']}")
        return correct, feedback


# AI-powered analysis via OpenAI (optional enhancement)
def analyze_with_ai(text: str, difficulty: Difficulty, api_key: str) -> GrammarAnalysis | None:
    """Use OpenAI API for deeper grammar analysis. Returns None on failure."""
    try:
        import urllib.request
        import urllib.error

        level_name = DIFFICULTY_LABELS.get(difficulty, "SFI")
        prompt = f"""Du är en svensk grammatiklärare. Analysera följande text skriven av en
elev på nivå {level_name}. Svara på lättläst svenska.

Text: "{text}"

Svara i JSON med dessa fält:
- "corrected": den korrigerade texten
- "errors": lista med objekt {{"type": "feltyp", "description": "beskrivning på lättläst svenska"}}
- "explanation": en förklaring på lättläst svenska (max 3 meningar)
- "score": poäng 0-100
"""
        data = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        content = json.loads(result["choices"][0]["message"]["content"])
        errors = [(e["type"], e["description"]) for e in content.get("errors", [])]
        return GrammarAnalysis(
            original=text,
            corrected=content.get("corrected", text),
            errors=errors,
            explanation=content.get("explanation", ""),
            score=content.get("score", 50),
        )
    except Exception:
        return None
