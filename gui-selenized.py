"""
Launcher direto com o tema Selenized pré-selecionado.
"""

import sys
from PyQt6.QtWidgets import QApplication
from nmap_gui.window import NmapGUI


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = NmapGUI()
    window.theme_combo.setCurrentText("Selenized")
    window.apply_theme("Selenized")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()