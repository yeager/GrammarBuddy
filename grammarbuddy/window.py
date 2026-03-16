"""Huvudfönster för GrammarBuddy."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango  # noqa: E402

from .grammar_engine import (
    GrammarEngine, Difficulty, DIFFICULTY_LABELS,
    ExerciseMode, MODE_LABELS, analyze_with_ai,
)
from .progress import (
    load_progress, record_exercise, record_analysis, get_accuracy,
    load_settings, save_settings,
)

import gettext
import os

# i18n setup
LOCALE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "po")
try:
    lang = gettext.translation("grammarbuddy", LOCALE_DIR, languages=["sv"])
    lang.install()
    _ = lang.gettext
except FileNotFoundError:
    _ = gettext.gettext


class GrammarBuddyWindow(Adw.ApplicationWindow):
    """Huvudfönster."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.engine = GrammarEngine()
        self.progress = load_progress()
        self.settings = load_settings()
        self.current_exercise = None

        self.set_title("GrammarBuddy – Svensk grammatikträning")
        self.set_default_size(900, 700)

        self._build_ui()
        self._apply_settings()

    def _build_ui(self):
        """Bygg hela UI:t."""
        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)

        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)

        # Title
        title = Adw.WindowTitle(
            title="GrammarBuddy",
            subtitle="Svensk grammatikträning"
        )
        header.set_title_widget(title)

        # Settings button
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text(_("Settings"))
        settings_btn.connect("clicked", self._on_settings)
        header.pack_end(settings_btn)

        # Stats button
        stats_btn = Gtk.Button(icon_name="view-list-symbolic")
        stats_btn.set_tooltip_text(_("Statistics"))
        stats_btn.connect("clicked", self._on_show_stats)
        header.pack_end(stats_btn)

        # Main content with stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_box.append(self.stack)

        # Stack switcher in header
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.stack)
        header.pack_start(switcher)

        # Page 1: Free analysis
        self._build_analysis_page()

        # Page 2: Exercises
        self._build_exercise_page()

        # Bottom bar with progress
        self._build_progress_bar()

    def _build_analysis_page(self):
        """Sida för fri textanalys."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(16)
        page.set_margin_bottom(16)
        page.set_margin_start(16)
        page.set_margin_end(16)

        self.stack.add_titled(page, "analysis", _("Textanalys"))

        # Instructions
        intro = Gtk.Label(
            label=_("Write a sentence in Swedish. GrammarBuddy helps you with grammar!"),
            wrap=True,
        )
        intro.add_css_class("title-4")
        page.append(intro)

        # Difficulty selector
        diff_box = Gtk.Box(spacing=8)
        diff_box.set_halign(Gtk.Align.CENTER)
        diff_label = Gtk.Label(label=_("Level:"))
        diff_box.append(diff_label)

        self.diff_dropdown = Gtk.DropDown.new_from_strings(
            [DIFFICULTY_LABELS[d] for d in Difficulty]
        )
        self.diff_dropdown.set_selected(self.settings.get("difficulty", 0))
        diff_box.append(self.diff_dropdown)
        page.append(diff_box)

        # Text input
        frame = Gtk.Frame()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(120)
        scrolled.set_vexpand(True)

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_left_margin(8)
        self.text_view.set_right_margin(8)
        self.text_view.set_top_margin(8)
        self.text_view.set_bottom_margin(8)
        self.text_view.get_buffer().set_text(_("Write your opinion here..."))

        scrolled.set_child(self.text_view)
        frame.set_child(scrolled)
        page.append(frame)

        # Analyze button
        btn_box = Gtk.Box(spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)

        analyze_btn = Gtk.Button(label=_("Analysera ✏️"))
        analyze_btn.add_css_class("suggested-action")
        analyze_btn.add_css_class("pill")
        analyze_btn.connect("clicked", self._on_analyze)
        btn_box.append(analyze_btn)

        clear_btn = Gtk.Button(label=_("Clear"))
        clear_btn.connect("clicked", self._on_clear)
        btn_box.append(clear_btn)

        page.append(btn_box)

        # Results area
        self.results_frame = Gtk.Frame(label=_("Resultat"))
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_min_content_height(150)
        results_scroll.set_vexpand(True)

        self.results_label = Gtk.Label(
            label=_("The results are shown here after analysis."),
            wrap=True,
            selectable=True,
        )
        self.results_label.set_xalign(0)
        self.results_label.set_margin_top(8)
        self.results_label.set_margin_bottom(8)
        self.results_label.set_margin_start(8)
        self.results_label.set_margin_end(8)

        results_scroll.set_child(self.results_label)
        self.results_frame.set_child(results_scroll)
        page.append(self.results_frame)

        # Corrected text
        self.corrected_frame = Gtk.Frame(label=_("Proposed correction"))
        self.corrected_label = Gtk.Label(wrap=True, selectable=True)
        self.corrected_label.set_xalign(0)
        self.corrected_label.set_margin_top(8)
        self.corrected_label.set_margin_bottom(8)
        self.corrected_label.set_margin_start(8)
        self.corrected_label.set_margin_end(8)
        self.corrected_frame.set_child(self.corrected_label)
        page.append(self.corrected_frame)
        self.corrected_frame.set_visible(False)

        # Score indicator
        self.score_bar = Gtk.LevelBar()
        self.score_bar.set_min_value(0)
        self.score_bar.set_max_value(100)
        self.score_bar.set_value(0)
        self.score_bar.set_margin_top(8)
        page.append(Gtk.Label(label=_("Points:"), xalign=0))
        page.append(self.score_bar)

    def _build_exercise_page(self):
        """Sida för övningar."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(16)
        page.set_margin_bottom(16)
        page.set_margin_start(16)
        page.set_margin_end(16)

        self.stack.add_titled(page, "exercises", _("Exercises"))

        # Mode selector
        mode_box = Gtk.Box(spacing=8)
        mode_box.set_halign(Gtk.Align.CENTER)
        mode_label = Gtk.Label(label=_("Type of exercise:"))
        mode_box.append(mode_label)

        mode_strings = [MODE_LABELS[m] for m in
                        [ExerciseMode.SPELLING, ExerciseMode.SENTENCE,
                         ExerciseMode.TENSE, ExerciseMode.WORD_ORDER]]
        self.mode_dropdown = Gtk.DropDown.new_from_strings(mode_strings)
        mode_box.append(self.mode_dropdown)
        page.append(mode_box)

        # Exercise display
        self.exercise_frame = Gtk.Frame()
        ex_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        ex_box.set_margin_top(12)
        ex_box.set_margin_bottom(12)
        ex_box.set_margin_start(12)
        ex_box.set_margin_end(12)

        self.exercise_label = Gtk.Label(
            label=_("Press \'New exercise\' to start!"),
            wrap=True,
        )
        self.exercise_label.add_css_class("title-3")
        ex_box.append(self.exercise_label)

        # Answer input
        self.answer_entry = Gtk.Entry()
        self.answer_entry.set_placeholder_text(_("Write your answer here..."))
        self.answer_entry.connect("activate", self._on_check_answer)
        ex_box.append(self.answer_entry)

        # Buttons
        ex_btn_box = Gtk.Box(spacing=8)
        ex_btn_box.set_halign(Gtk.Align.CENTER)

        check_btn = Gtk.Button(label=_("Kontrollera"))
        check_btn.add_css_class("suggested-action")
        check_btn.connect("clicked", self._on_check_answer)
        ex_btn_box.append(check_btn)

        new_btn = Gtk.Button(label=_("New exercise"))
        new_btn.connect("clicked", self._on_new_exercise)
        ex_btn_box.append(new_btn)

        hint_btn = Gtk.Button(label=_("Clue"))
        hint_btn.connect("clicked", self._on_show_hint)
        ex_btn_box.append(hint_btn)

        ex_box.append(ex_btn_box)

        # Feedback area
        self.exercise_feedback = Gtk.Label(wrap=True, selectable=True)
        self.exercise_feedback.set_xalign(0)
        self.exercise_feedback.add_css_class("body")
        ex_box.append(self.exercise_feedback)

        self.exercise_frame.set_child(ex_box)
        page.append(self.exercise_frame)

        # Streak display
        streak_box = Gtk.Box(spacing=8)
        streak_box.set_halign(Gtk.Align.CENTER)
        self.streak_label = Gtk.Label(label=self._streak_text())
        self.streak_label.add_css_class("title-4")
        streak_box.append(self.streak_label)
        page.append(streak_box)

    def _build_progress_bar(self):
        """Bygg statusrad med framsteg."""
        status_box = Gtk.Box(spacing=12)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        status_box.set_margin_start(16)
        status_box.set_margin_end(16)

        self.progress_label = Gtk.Label(
            label=self._progress_text(),
        )
        self.progress_label.set_hexpand(True)
        self.progress_label.set_xalign(0)
        status_box.append(self.progress_label)

        ai_label = Gtk.Label()
        if self.engine.ai_available:
            ai_label.set_label("🤖 AI aktiv")
        else:
            ai_label.set_label("📚 Lokal analys")
        status_box.append(ai_label)

        self.main_box.append(Gtk.Separator())
        self.main_box.append(status_box)

    def _streak_text(self) -> str:
        streak = self.progress.get("streak", 0)
        best = self.progress.get("best_streak", 0)
        return f"🔥 Svit: {streak} | Bästa: {best}"

    def _progress_text(self) -> str:
        total = self.progress.get("total_exercises", 0)
        acc = get_accuracy(self.progress)
        analyses = self.progress.get("total_analyses", 0)
        return (f"Övningar: {total} | "
                f"Rätt: {acc:.0f}% | "
                f"Analyser: {analyses}")

    def _apply_settings(self):
        self.diff_dropdown.set_selected(self.settings.get("difficulty", 0))

    def _get_difficulty(self) -> Difficulty:
        return Difficulty(self.diff_dropdown.get_selected())

    def _get_mode(self) -> str:
        modes = [ExerciseMode.SPELLING, ExerciseMode.SENTENCE,
                 ExerciseMode.TENSE, ExerciseMode.WORD_ORDER]
        idx = self.mode_dropdown.get_selected()
        return modes[min(idx, len(modes) - 1)]

    # --- Signal handlers ---

    def _on_analyze(self, _btn):
        """Analysera texten."""
        buf = self.text_view.get_buffer()
        start, end = buf.get_bounds()
        text = buf.get_text(start, end, False)

        if not text.strip():
            return

        difficulty = self._get_difficulty()

        # Try AI first if available
        result = None
        if self.engine.ai_available:
            result = analyze_with_ai(text, difficulty, os.environ.get("OPENAI_API_KEY", ""))

        if result is None:
            result = self.engine.analyze(text, difficulty)

        # Display results
        self.results_label.set_label(result.explanation)
        self.score_bar.set_value(result.score)

        if result.corrected != result.original:
            self.corrected_label.set_label(result.corrected)
            self.corrected_frame.set_visible(True)
        else:
            self.corrected_frame.set_visible(False)

        # Record
        record_analysis(self.progress, result.score)
        self._update_status()

    def _on_clear(self, _btn):
        """Rensa textfältet."""
        self.text_view.get_buffer().set_text("")
        self.results_label.set_label(_("The results are shown here after analysis."))
        self.corrected_frame.set_visible(False)
        self.score_bar.set_value(0)

    def _on_new_exercise(self, _btn):
        """Ladda ny övning."""
        difficulty = self._get_difficulty()
        mode = self._get_mode()

        exercise = self.engine.get_exercise(difficulty, mode)
        if exercise:
            self.current_exercise = exercise
            self.exercise_label.set_label(exercise["prompt"])
            self.answer_entry.set_text("")
            self.exercise_feedback.set_label("")
        else:
            self.exercise_label.set_label(
                _("No exercises available for this combination.")
            )

    def _on_check_answer(self, _widget):
        """Kontrollera svar."""
        if not self.current_exercise:
            self.exercise_feedback.set_label(_("Start an exercise first!"))
            return

        answer = self.answer_entry.get_text()
        if not answer.strip():
            return

        correct, feedback = self.engine.check_exercise_answer(
            self.current_exercise, answer
        )

        self.exercise_feedback.set_label(feedback)

        mode = self._get_mode()
        difficulty = self._get_difficulty()
        record_exercise(self.progress, mode, int(difficulty), correct)
        self._update_status()

    def _on_show_hint(self, _btn):
        """Visa ledtråd."""
        if self.current_exercise:
            self.exercise_feedback.set_label(
                f"💡 {self.current_exercise.get('hint', 'Ingen ledtråd tillgänglig.')}"
            )

    def _on_show_stats(self, _btn):
        """Visa statistikdialog."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Din statistik"),
            body=self._stats_text(),
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def _on_settings(self, _btn):
        """Visa inställningar."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Settings"),
            body=_("Settings are automatically saved.\n\n"
                   "AI-analys: Sätt miljövariabeln OPENAI_API_KEY\n"
                   "för att aktivera AI-baserad grammatikanalys.\n\n"
                   f"AI-status: {'Aktiv ✓' if self.engine.ai_available else 'Ej aktiv'}"),
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def _stats_text(self) -> str:
        p = self.progress
        acc = get_accuracy(p)
        avg_score = p.get("average_score", 0)
        lines = [
            f"Totalt antal övningar: {p.get('total_exercises', 0)}",
            f"Rätta svar: {p.get('correct_answers', 0)}",
            f"Träffsäkerhet: {acc:.1f}%",
            f"Bästa svit: {p.get('best_streak', 0)}",
            f"Antal analyser: {p.get('total_analyses', 0)}",
            f"Medelpoäng: {avg_score:.0f}",
            "",
            "Per övningstyp:",
        ]
        for mode, label in MODE_LABELS.items():
            data = p.get("by_mode", {}).get(mode, {})
            total = data.get("total", 0)
            correct = data.get("correct", 0)
            if total > 0:
                lines.append(f"  {label}: {correct}/{total} ({correct/total*100:.0f}%)")
        return "\n".join(lines)

    def _update_status(self):
        """Uppdatera statusraden."""
        self.progress_label.set_label(self._progress_text())
        self.streak_label.set_label(self._streak_text())

        # Save settings
        self.settings["difficulty"] = int(self._get_difficulty())
        self.settings["mode"] = self._get_mode()
        save_settings(self.settings)
