"""Tests for command-line interface selection."""

from galactic_trader.__main__ import build_parser


def test_pygame_is_the_default_interface() -> None:
    """Starting without options selects the graphical interface."""
    assert build_parser().parse_args([]).ui == "pygame"


def test_terminal_interface_can_still_be_selected() -> None:
    """The existing terminal interface remains available explicitly."""
    assert build_parser().parse_args(["--ui", "terminal"]).ui == "terminal"
