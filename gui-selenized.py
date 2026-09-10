"""
Interface gráfica PyQt6 para o Nmap Scanner.
Tema Selenized Dark (oficial - Jan Warchoł).
"""

import sys
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QProgressBar, QCheckBox, QSpinBox
)

from nmap_logic import NmapLogic, NmapError


# ============================================================
# Estilo Selenized Dark (oficial)
# Cores extraídas de: https://github.com/jan-warchol/selenized
# ============================================================
SELENIZED_STYLE = """
/* ===== Cores base Selenized Dark =====
   bg_0   #103c48
   bg_1   #184956
   bg_2   #2d5b69
   dim_0  #72898f
   fg_0   #adbcbc
   fg_1   #cad8d9
   blue   #4695f7
   cyan   #41c7b9
   green  #75b938
   yellow #dbb32d
   red    #fa5750
*/

/* ===== Fundo geral ===== */
QMainWindow, QWidget {
    background-color: #103c48;
    color: #adbcbc;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 13px;
}

/* ===== GroupBox ===== */
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

/* ===== Labels ===== */
QLabel {
    color: #adbcbc;
    background: transparent;
}

/* ===== LineEdit / SpinBox ===== */
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

/* ===== ComboBox ===== */
QComboBox {
    background-color: #184956;
    border: 1px solid #2d5b69;
    border-radius: 4px;
    padding: 5px 8px;
    color: #cad8d9;
    min-height: 22px;
}

QComboBox:hover {
    border: 1px solid #4695f7;
}

QComboBox:focus {
    border: 1px solid #4695f7;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #adbcbc;
    width: 0;
    height: 0;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #184956;
    border: 1px solid #2d5b69;
    selection-background-color: #4695f7;
    selection-color: #103c48;
    color: #cad8d9;
    outline: none;
}

/* ===== Botões ===== */
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

/* Botão principal (Iniciar Scan) */
QPushButton#scanButton {
    background-color: #4695f7;
    border: 1px solid #58a3ff;
    color: #103c48;
    font-weight: bold;
}

QPushButton#scanButton:hover {
    background-color: #58a3ff;
    border: 1px solid #6ab0ff;
    color: #103c48;
}

QPushButton#scanButton:pressed {
    background-color: #3a7fd0;
}

QPushButton#scanButton:disabled {
    background-color: #14343e;
    border: 1px solid #2d5b69;
    color: #72898f;
}

/* ===== CheckBox ===== */
QCheckBox {
    color: #adbcbc;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #2d5b69;
    border-radius: 3px;
    background-color: #184956;
}

QCheckBox::indicator:checked {
    background-color: #4695f7;
    border: 1px solid #58a3ff;
}

QCheckBox::indicator:hover {
    border: 1px solid #4695f7;
}

/* ===== TextEdit (área de saída) ===== */
QTextEdit {
    background-color: #0d2f38;
    border: 1px solid #2d5b69;
    border-radius: 5px;
    color: #adbcbc;
    selection-background-color: #4695f7;
    selection-color: #103c48;
    padding: 6px;
}

/* ===== ProgressBar ===== */
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

/* ===== StatusBar ===== */
QStatusBar {
    background-color: #0d2f38;
    color: #72898f;
    border-top: 1px solid #2d5b69;
}

QStatusBar::item {
    border: none;
}

/* ===== Scrollbars ===== */
QScrollBar:vertical {
    background: #103c48;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2d5b69;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #3a6b7a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #103c48;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #2d5b69;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #3a6b7a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===== MessageBox ===== */
QMessageBox {
    background-color: #103c48;
    color: #adbcbc;
}

QMessageBox QLabel {
    color: #adbcbc;
}
"""


class ScanWorker(QThread):
    """Worker thread para executar o scan sem travar a interface."""

    finished = pyqtSignal(str, str, int)   # stdout, stderr, returncode
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
        self.setWindowTitle("Nmap GUI — Selenized Dark")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)

        try:
            self.logic = NmapLogic()
        except NmapError as e:
            QMessageBox.critical(None, "Erro fatal", str(e))
            sys.exit(1)

        self.worker = None
        self._build_ui()
        self._show_nmap_version()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(14, 14, 14, 14)

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

        # Status bar
        self.statusBar().showMessage("Pronto")

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

    # Aplica o tema Selenized Dark
    app.setStyle("Fusion")
    app.setStyleSheet(SELENIZED_STYLE)

    window = NmapGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()