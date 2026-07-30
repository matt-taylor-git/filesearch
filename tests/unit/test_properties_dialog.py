"""Tests for hover text in the file properties dialog."""

from PyQt6.QtWidgets import QLabel

from filesearch.ui.dialogs.properties_dialog import PropertiesDialog


def test_property_values_reveal_their_exact_text(qtbot, tmp_path):
    """Data-bearing property labels expose their complete displayed value."""
    file_path = tmp_path / "a-file-with-a-long-name.txt"
    file_path.write_text("tooltip test", encoding="utf-8")
    dialog = PropertiesDialog(file_path)
    qtbot.addWidget(dialog)

    path_label = next(
        label for label in dialog.findChildren(QLabel) if label.text() == str(file_path)
    )

    assert path_label.toolTip() == str(file_path)


def test_checksum_tooltip_tracks_the_calculated_value(qtbot, tmp_path):
    """A newly calculated checksum replaces the placeholder hover text."""
    file_path = tmp_path / "checksums.txt"
    file_path.write_text("tooltip test", encoding="utf-8")
    dialog = PropertiesDialog(file_path)
    qtbot.addWidget(dialog)

    dialog.on_checksum_calculated("MD5", "abc123")

    assert dialog.md5_label.toolTip() == "ABC123"
