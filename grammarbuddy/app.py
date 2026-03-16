"""GrammarBuddy Gtk.Application."""

import sys

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio  # noqa: E402

from . import __app_id__
from .window import GrammarBuddyWindow


class GrammarBuddyApp(Adw.Application):
    """Huvudapplikation."""

    def __init__(self):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = GrammarBuddyWindow(application=self)
        win.present()


def main():
    app = GrammarBuddyApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
