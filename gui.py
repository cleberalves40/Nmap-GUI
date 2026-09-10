"""
Interface gráfica PyQt6 para o Nmap Scanner.
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
        self.setWindowTitle("Nmap GUI - Python 3.12 + PyQt6")
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
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # === Grupo de configuração ===
        config_group = QGroupBox("Configuração do Scan")
        config_layout = QVBoxLayout(config_group)

        # Alvo
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Alvo:"))
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Ex: 192.168.1.1  ou  scanme.nmap.org  ou  192.168.1.0/24")
        target_layout.addWidget(self.target_edit)
        config_layout.addLayout(target_layout)

        # Portas + Tipo de scan + Timing
        options_layout = QHBoxLayout()

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
        self.scan_btn = QPushButton("Iniciar Scan")
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
        self.progress.setRange(0, 0)          # indeterminado
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
        # Rola para o final
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)

    def clear_output(self):
        self.output_text.clear()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # visual mais moderno e consistente

    window = NmapGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()