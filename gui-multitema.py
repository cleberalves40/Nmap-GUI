"""
Interface gráfica PyQt6 para o Nmap Scanner.
Com seletor de temas: Padrão, Charcoal, Selenized e Catppuccin Frappé.
"""

import sys
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QProgressBar, QCheckBox, QSpinBox
)

from nmap_logic import NmapLogic, NmapError


# ============================================================
# Temas (QSS)
# ============================================================

# ---------- PADRÃO (claro / neutro) ----------
STYLE_PADRAO = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #222222;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #222222;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #ffffff;
}
QLabel { color: #222222; background: transparent; }
QLineEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 5px 8px;
    color: #222222;
    selection-background-color: #3a7bd5;
    selection-color: #ffffff;
}
QLineEdit:focus, QSpinBox:focus { border: 1px solid #3a7bd5; }
QComboBox {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 5px 8px;
    color: #222222;
    min-height: 22px;
}
QComboBox:hover, QComboBox:focus { border: 1px solid #3a7bd5; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #555555;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    selection-background-color: #3a7bd5;
    selection-color: #ffffff;
    color: #222222;
}
QPushButton {
    background-color: #e8e8e8;
    border: 1px solid #c0c0c0;
    border-radius: 5px;
    padding: 6px 16px;
    color: #222222;
    font-weight: 500;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #d8d8d8;
    border: 1px solid #3a7bd5;
}
QPushButton:pressed { background-color: #c8c8c8; }
QPushButton:disabled {
    background-color: #eeeeee;
    color: #999999;
    border: 1px solid #d0d0d0;
}
QPushButton#scanButton {
    background-color: #3a7bd5;
    border: 1px solid #2a6bc5;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#scanButton:hover {
    background-color: #4a8be5;
    border: 1px solid #3a7bd5;
}
QPushButton#scanButton:pressed { background-color: #2a6bc5; }
QPushButton#scanButton:disabled {
    background-color: #eeeeee;
    color: #999999;
    border: 1px solid #d0d0d0;
}
QCheckBox { color: #222222; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #3a7bd5;
    border: 1px solid #2a6bc5;
}
QCheckBox::indicator:hover { border: 1px solid #3a7bd5; }
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 5px;
    color: #222222;
    selection-background-color: #3a7bd5;
    selection-color: #ffffff;
    padding: 6px;
}
QProgressBar {
    background-color: #e8e8e8;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    text-align: center;
    color: #222222;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #3a7bd5;
    border-radius: 3px;
}
QStatusBar {
    background-color: #e8e8e8;
    color: #555555;
    border-top: 1px solid #d0d0d0;
}
QScrollBar:vertical {
    background: #f5f5f5;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #c0c0c0;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #a0a0a0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #f5f5f5;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #c0c0c0;
    border-radius: 6px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #a0a0a0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""

# ---------- CHARCOAL (GNS3) ----------
STYLE_CHARCOAL = """
QMainWindow, QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #323232;
    border: 1px solid #4a4a4a;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #f0f0f0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #d0d0d0;
    background-color: #323232;
}
QLabel { color: #d8d8d8; background: transparent; }
QLineEdit, QSpinBox {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 8px;
    color: #e8e8e8;
    selection-background-color: #4a7aaa;
    selection-color: #ffffff;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #6a9ac0;
    background-color: #404040;
}
QLineEdit:disabled, QSpinBox:disabled {
    background-color: #2f2f2f;
    color: #888888;
    border: 1px solid #444444;
}
QComboBox {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 8px;
    color: #e8e8e8;
    min-height: 22px;
}
QComboBox:hover, QComboBox:focus { border: 1px solid #6a9ac0; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #c0c0c0;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    selection-background-color: #4a7aaa;
    selection-color: #ffffff;
    color: #e0e0e0;
}
QPushButton {
    background-color: #404040;
    border: 1px solid #5a5a5a;
    border-radius: 5px;
    padding: 6px 16px;
    color: #e8e8e8;
    font-weight: 500;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #4a4a4a;
    border: 1px solid #6a9ac0;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #353535;
    border: 1px solid #4a7aaa;
}
QPushButton:disabled {
    background-color: #333333;
    border: 1px solid #444444;
    color: #777777;
}
QPushButton#scanButton {
    background-color: #3d5a80;
    border: 1px solid #4a7aaa;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#scanButton:hover {
    background-color: #4a6f9a;
    border: 1px solid #6a9ac0;
}
QPushButton#scanButton:pressed { background-color: #2f4a6a; }
QPushButton#scanButton:disabled {
    background-color: #333333;
    border: 1px solid #444444;
    color: #777777;
}
QCheckBox { color: #d8d8d8; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #5a5a5a;
    border-radius: 3px;
    background-color: #3a3a3a;
}
QCheckBox::indicator:checked {
    background-color: #4a7aaa;
    border: 1px solid #6a9ac0;
}
QCheckBox::indicator:hover { border: 1px solid #6a9ac0; }
QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #4a4a4a;
    border-radius: 5px;
    color: #d0d0d0;
    selection-background-color: #4a7aaa;
    selection-color: #ffffff;
    padding: 6px;
}
QProgressBar {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #4a7aaa;
    border-radius: 3px;
}
QStatusBar {
    background-color: #252525;
    color: #b0b0b0;
    border-top: 1px solid #3a3a3a;
}
QScrollBar:vertical {
    background: #2b2b2b;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #6a6a6a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #2b2b2b;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #555555;
    border-radius: 6px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #6a6a6a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""

# ---------- SELENIZED DARK ----------
STYLE_SELENIZED = """
QMainWindow, QWidget {
    background-color: #103c48;
    color: #adbcbc;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #184956;
    border: 1px solid #2d5b69;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #cad8d9;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #cad8d9;
    background-color: #184956;
}
QLabel { color: #adbcbc; background: transparent; }
QLineEdit, QSpinBox {
    background-color: #184956;
    border: 1px solid #2d5b69;
    border-radius: 4px;
    padding: 5px 8px;
    color: #cad8d9;
    selection-background-color: #4695f7;
    selection-color: #103c48;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #4695f7;
    background-color: #1a5260;
}
QLineEdit:disabled, QSpinBox:disabled {
    background-color: #14343e;
    color: #72898f;
    border: 1px solid #2d5b69;
}
QComboBox {
    background-color: #184956;
    border: 1px solid #2d5b69;
    border-radius: 4px;
    padding: 5px 8px;
    color: #cad8d9;
    min-height: 22px;
}
QComboBox:hover, QComboBox:focus { border: 1px solid #4695f7; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #adbcbc;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #184956;
    border: 1px solid #2d5b69;
    selection-background-color: #4695f7;
    selection-color: #103c48;
    color: #cad8d9;
}
QPushButton {
    background-color: #2d5b69;
    border: 1px solid #3a6b7a;
    border-radius: 5px;
    padding: 6px 16px;
    color: #cad8d9;
    font-weight: 500;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #3a6b7a;
    border: 1px solid #4695f7;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #255060;
    border: 1px solid #41c7b9;
}
QPushButton:disabled {
    background-color: #14343e;
    border: 1px solid #2d5b69;
    color: #72898f;
}
QPushButton#scanButton {
    background-color: #4695f7;
    border: 1px solid #58a3ff;
    color: #103c48;
    font-weight: bold;
}
QPushButton#scanButton:hover {
    background-color: #58a3ff;
    border: 1px solid #6ab0ff;
}
QPushButton#scanButton:pressed { background-color: #3a7fd0; }
QPushButton#scanButton:disabled {
    background-color: #14343e;
    border: 1px solid #2d5b69;
    color: #72898f;
}
QCheckBox { color: #adbcbc; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #2d5b69;
    border-radius: 3px;
    background-color: #184956;
}
QCheckBox::indicator:checked {
    background-color: #4695f7;
    border: 1px solid #58a3ff;
}
QCheckBox::indicator:hover { border: 1px solid #4695f7; }
QTextEdit {
    background-color: #0d2f38;
    border: 1px solid #2d5b69;
    border-radius: 5px;
    color: #adbcbc;
    selection-background-color: #4695f7;
    selection-color: #103c48;
    padding: 6px;
}
QProgressBar {
    background-color: #184956;
    border: 1px solid #2d5b69;
    border-radius: 4px;
    text-align: center;
    color: #cad8d9;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #41c7b9;
    border-radius: 3px;
}
QStatusBar {
    background-color: #0d2f38;
    color: #72898f;
    border-top: 1px solid #2d5b69;
}
QScrollBar:vertical {
    background: #103c48;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #2d5b69;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #3a6b7a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #103c48;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #2d5b69;
    border-radius: 6px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #3a6b7a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""

# ---------- CATPPUCCIN FRAPPÉ ----------
STYLE_CATPPUCCIN = """
QMainWindow, QWidget {
    background-color: #303446;
    color: #c6d0f5;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #292c3c;
    border: 1px solid #414559;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #c6d0f5;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #b5bfe2;
    background-color: #292c3c;
}
QLabel { color: #c6d0f5; background: transparent; }
QLineEdit, QSpinBox {
    background-color: #414559;
    border: 1px solid #51576d;
    border-radius: 4px;
    padding: 5px 8px;
    color: #c6d0f5;
    selection-background-color: #8caaee;
    selection-color: #232634;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #8caaee;
    background-color: #51576d;
}
QLineEdit:disabled, QSpinBox:disabled {
    background-color: #292c3c;
    color: #737994;
    border: 1px solid #414559;
}
QComboBox {
    background-color: #414559;
    border: 1px solid #51576d;
    border-radius: 4px;
    padding: 5px 8px;
    color: #c6d0f5;
    min-height: 22px;
}
QComboBox:hover, QComboBox:focus { border: 1px solid #8caaee; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #b5bfe2;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #414559;
    border: 1px solid #51576d;
    selection-background-color: #8caaee;
    selection-color: #232634;
    color: #c6d0f5;
}
QPushButton {
    background-color: #51576d;
    border: 1px solid #626880;
    border-radius: 5px;
    padding: 6px 16px;
    color: #c6d0f5;
    font-weight: 500;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #626880;
    border: 1px solid #8caaee;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #414559;
    border: 1px solid #81c8be;
}
QPushButton:disabled {
    background-color: #292c3c;
    border: 1px solid #414559;
    color: #737994;
}
QPushButton#scanButton {
    background-color: #8caaee;
    border: 1px solid #babbf1;
    color: #232634;
    font-weight: bold;
}
QPushButton#scanButton:hover {
    background-color: #babbf1;
    border: 1px solid #c6d0f5;
}
QPushButton#scanButton:pressed { background-color: #7a9adf; }
QPushButton#scanButton:disabled {
    background-color: #292c3c;
    border: 1px solid #414559;
    color: #737994;
}
QCheckBox { color: #c6d0f5; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #51576d;
    border-radius: 3px;
    background-color: #414559;
}
QCheckBox::indicator:checked {
    background-color: #8caaee;
    border: 1px solid #babbf1;
}
QCheckBox::indicator:hover { border: 1px solid #8caaee; }
QTextEdit {
    background-color: #232634;
    border: 1px solid #414559;
    border-radius: 5px;
    color: #c6d0f5;
    selection-background-color: #8caaee;
    selection-color: #232634;
    padding: 6px;
}
QProgressBar {
    background-color: #414559;
    border: 1px solid #51576d;
    border-radius: 4px;
    text-align: center;
    color: #c6d0f5;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #81c8be;
    border-radius: 3px;
}
QStatusBar {
    background-color: #232634;
    color: #a5adce;
    border-top: 1px solid #414559;
}
QScrollBar:vertical {
    background: #303446;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #51576d;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #626880; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #303446;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #51576d;
    border-radius: 6px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #626880; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""


# Dicionário de temas
THEMES = {
    "Padrão": STYLE_PADRAO,
    "Charcoal": STYLE_CHARCOAL,
    "Selenized": STYLE_SELENIZED,
    "Catppuccin": STYLE_CATPPUCCIN,
}


class ScanWorker(QThread):
    """Worker thread para executar o scan sem travar a interface."""

    finished = pyqtSignal(str, str, int)
    error = pyqtSignal(str)

    def __init__(self, logic: NmapLogic, **kwargs):
        super().__init__()
        self.logic = logic
        self.kwargs = kwargs

    def run(self):
        try:
            stdout, stderr, code = self.logic.run_scan(**self.kwargs)
            self.finished.emit(stdout, stderr, code)
        except NmapError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Erro inesperado: {e}")


class NmapGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nmap GUI — Seletor de Temas")
        self.setMinimumSize(920, 680)
        self.resize(1020, 720)

        try:
            self.logic = NmapLogic()
        except NmapError as e:
            QMessageBox.critical(None, "Erro fatal", str(e))
            sys.exit(1)

        self.worker = None
        self.settings = QSettings("NmapGUI", "ThemeSelector")

        self._build_ui()
        self._load_theme()
        self._show_nmap_version()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # === Barra superior: Tema ===
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.theme_combo.setMinimumWidth(160)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        main_layout.addLayout(theme_layout)

        # === Grupo de configuração ===
        config_group = QGroupBox("Configuração do Scan")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Alvo
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Alvo:"))
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Ex: 192.168.1.1  ou  scanme.nmap.org  ou  192.168.1.0/24")
        target_layout.addWidget(self.target_edit)
        config_layout.addLayout(target_layout)

        # Portas + Tipo de scan + Timing
        options_layout = QHBoxLayout()
        options_layout.setSpacing(10)

        options_layout.addWidget(QLabel("Portas:"))
        self.ports_edit = QLineEdit()
        self.ports_edit.setPlaceholderText("Ex: 22,80,443  ou  1-1000  (vazio = padrão)")
        self.ports_edit.setMinimumWidth(180)
        options_layout.addWidget(self.ports_edit)

        options_layout.addWidget(QLabel("Tipo de Scan:"))
        self.scan_type_combo = QComboBox()
        for key, desc in self.logic.get_common_scan_types().items():
            self.scan_type_combo.addItem(f"{key}  —  {desc}", key)
        options_layout.addWidget(self.scan_type_combo)

        options_layout.addWidget(QLabel("Timing:"))
        self.timing_combo = QComboBox()
        for t in ["T0", "T1", "T2", "T3", "T4", "T5"]:
            self.timing_combo.addItem(t)
        self.timing_combo.setCurrentText("T3")
        options_layout.addWidget(self.timing_combo)

        config_layout.addLayout(options_layout)

        # Argumentos extras
        extra_layout = QHBoxLayout()
        extra_layout.addWidget(QLabel("Argumentos extras:"))
        self.extra_edit = QLineEdit()
        self.extra_edit.setPlaceholderText("Ex: -Pn -n --script=vuln  (opcional)")
        extra_layout.addWidget(self.extra_edit)
        config_layout.addLayout(extra_layout)

        # Opções adicionais
        extra_opts_layout = QHBoxLayout()
        self.xml_checkbox = QCheckBox("Saída em XML")
        extra_opts_layout.addWidget(self.xml_checkbox)

        extra_opts_layout.addWidget(QLabel("Timeout (segundos, 0 = sem limite):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600)
        self.timeout_spin.setValue(0)
        extra_opts_layout.addWidget(self.timeout_spin)
        extra_opts_layout.addStretch()
        config_layout.addLayout(extra_opts_layout)

        main_layout.addWidget(config_group)

        # === Botões ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.scan_btn = QPushButton("Iniciar Scan")
        self.scan_btn.setObjectName("scanButton")
        self.scan_btn.setMinimumHeight(36)
        self.scan_btn.clicked.connect(self.start_scan)

        self.stop_btn = QPushButton("Parar")
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)

        self.clear_btn = QPushButton("Limpar Saída")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.clicked.connect(self.clear_output)

        btn_layout.addWidget(self.scan_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # Progresso
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # === Área de saída ===
        output_group = QGroupBox("Resultado do Scan")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        output_layout.addWidget(self.output_text)

        main_layout.addWidget(output_group)

        self.statusBar().showMessage("Pronto")

    def apply_theme(self, theme_name: str):
        """Aplica o tema selecionado e salva a preferência."""
        style = THEMES.get(theme_name, STYLE_PADRAO)
        QApplication.instance().setStyleSheet(style)
        self.settings.setValue("theme", theme_name)
        self.setWindowTitle(f"Nmap GUI — {theme_name}")

    def _load_theme(self):
        """Carrega o último tema usado (ou Padrão)."""
        saved = self.settings.value("theme", "Padrão")
        if saved not in THEMES:
            saved = "Padrão"
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(saved)
        self.theme_combo.blockSignals(False)
        self.apply_theme(saved)

    def _show_nmap_version(self):
        try:
            version = self.logic.get_version()
            self.statusBar().showMessage(f"Nmap encontrado: {version}")
        except NmapError as e:
            self.statusBar().showMessage(str(e))

    def start_scan(self):
        target = self.target_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Atenção", "Informe um alvo válido.")
            return

        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Aguarde", "Já existe um scan em andamento.")
            return

        ports = self.ports_edit.text().strip()
        scan_type = self.scan_type_combo.currentData()
        timing = self.timing_combo.currentText()
        extra = self.extra_edit.text().strip()
        output_format = "xml" if self.xml_checkbox.isChecked() else "normal"
        timeout = self.timeout_spin.value() or None

        self.output_text.clear()
        self.output_text.append(">>> Iniciando scan...\n")
        self.output_text.append(f"Comando: nmap {scan_type} -{timing} "
                                f"{'-p ' + ports if ports else ''} "
                                f"{extra} {target}\n")
        self.output_text.append("-" * 60 + "\n")

        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setVisible(True)
        self.statusBar().showMessage("Scan em andamento...")

        self.worker = ScanWorker(
            self.logic,
            target=target,
            ports=ports,
            scan_type=scan_type,
            extra_args=extra,
            timing=timing,
            output_format=output_format,
            timeout=timeout
        )
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.error.connect(self.on_scan_error)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(2000)
            self.output_text.append("\n\n>>> Scan interrompido pelo usuário.\n")
            self._reset_ui()
            self.statusBar().showMessage("Scan interrompido")

    def on_scan_finished(self, stdout: str, stderr: str, returncode: int):
        self.output_text.append(stdout)
        if stderr:
            self.output_text.append("\n--- STDERR ---\n")
            self.output_text.append(stderr)

        self.output_text.append(f"\n>>> Scan finalizado (código de retorno: {returncode})\n")
        self._reset_ui()
        self.statusBar().showMessage(f"Scan concluído (código {returncode})")

    def on_scan_error(self, message: str):
        self.output_text.append(f"\n[ERRO] {message}\n")
        QMessageBox.critical(self, "Erro no Scan", message)
        self._reset_ui()
        self.statusBar().showMessage("Erro durante o scan")

    def _reset_ui(self):
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)

    def clear_output(self):
        self.output_text.clear()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # base limpa para os QSS

    window = NmapGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()