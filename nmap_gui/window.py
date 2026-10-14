"""
Interface gráfica PyQt6 para o Nmap Scanner.
Suporte a temas dinâmicos (Padrão, Charcoal, Selenized, Catppuccin) e streaming de saída em tempo real.
"""

import sys
import os
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QTextCursor, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QProgressBar, QCheckBox, QSpinBox,
    QFileDialog, QStatusBar
)

from .logic import NmapLogic, NmapError
from .themes import THEMES, STYLE_PADRAO, get_theme_names, get_theme_stylesheet


class ScanWorker(QThread):
    """
    Worker thread que executa o Nmap via subprocess.Popen
    e envia linhas de saída em tempo real para a interface gráfica.
    """
    line_received = pyqtSignal(str)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, logic: NmapLogic, **kwargs):
        super().__init__()
        self.logic = logic
        self.kwargs = kwargs
        self.process = None
        self._is_stopped = False

    def run(self):
        try:
            self.process = self.logic.create_process(**self.kwargs)
            # Ler saída em tempo real
            while True:
                if self._is_stopped:
                    break
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                if line:
                    self.line_received.emit(line)

            # Ler possíveis linhas residuais do stderr
            if self.process.stderr:
                err = self.process.stderr.read()
                if err:
                    self.line_received.emit(f"\n[STDERR]\n{err}")

            returncode = self.process.poll() if self.process else 0
            if not self._is_stopped:
                self.finished.emit(returncode if returncode is not None else 0)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Interrompe o processo do Nmap de forma limpa."""
        self._is_stopped = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass


class NmapGUI(QMainWindow):
    """Janela principal da aplicação Nmap GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nmap GUI")
        self.setMinimumSize(940, 680)
        self.resize(1040, 740)

        self.logic = NmapLogic()
        self.worker: Optional[ScanWorker] = None
        self.settings = QSettings("NmapGUI", "NmapApp")

        self._build_ui()
        self._load_saved_settings()
        self._check_nmap_status()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # === Barra superior: Tema e Configurações ===
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(get_theme_names())
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.theme_combo.setMinimumWidth(160)
        top_bar.addWidget(self.theme_combo)

        top_bar.addStretch()

        self.save_btn = QPushButton("Salvar Saída...")
        self.save_btn.clicked.connect(self.save_output_to_file)
        top_bar.addWidget(self.save_btn)

        main_layout.addLayout(top_bar)

        # === Grupo de configuração do Scan ===
        config_group = QGroupBox("Configuração do Scan")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Campo: Alvo
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Alvo:"))
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Ex: 192.168.1.1, scanme.nmap.org ou 10.0.0.0/24")
        self.target_edit.returnPressed.connect(self.start_scan)
        target_layout.addWidget(self.target_edit)
        config_layout.addLayout(target_layout)

        # Campos: Portas, Tipo de Scan, Timing
        opts_layout = QHBoxLayout()
        opts_layout.setSpacing(10)

        opts_layout.addWidget(QLabel("Portas:"))
        self.ports_edit = QLineEdit()
        self.ports_edit.setPlaceholderText("Ex: 22,80,443 ou 1-1000 (vazio = portas padrão)")
        self.ports_edit.setMinimumWidth(180)
        opts_layout.addWidget(self.ports_edit)

        opts_layout.addWidget(QLabel("Tipo de Scan:"))
        self.scan_type_combo = QComboBox()
        for key, desc in self.logic.get_common_scan_types().items():
            self.scan_type_combo.addItem(f"{key} — {desc}", key)
        opts_layout.addWidget(self.scan_type_combo)

        opts_layout.addWidget(QLabel("Timing:"))
        self.timing_combo = QComboBox()
        for t in ["T0", "T1", "T2", "T3", "T4", "T5"]:
            self.timing_combo.addItem(t)
        self.timing_combo.setCurrentText("T3")
        opts_layout.addWidget(self.timing_combo)

        config_layout.addLayout(opts_layout)

        # Campo: Argumentos extras
        extra_layout = QHBoxLayout()
        extra_layout.addWidget(QLabel("Argumentos extras:"))
        self.extra_edit = QLineEdit()
        self.extra_edit.setPlaceholderText("Ex: -Pn -n --script=vuln,banner (opcional)")
        extra_layout.addWidget(self.extra_edit)
        config_layout.addLayout(extra_layout)

        # Opções adicionais
        extra_opts_layout = QHBoxLayout()
        self.xml_checkbox = QCheckBox("Saída em formato XML (-oX)")
        extra_opts_layout.addWidget(self.xml_checkbox)

        extra_opts_layout.addSpacing(20)
        extra_opts_layout.addWidget(QLabel("Timeout (segundos, 0 = sem limite):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 3600)
        self.timeout_spin.setValue(0)
        extra_opts_layout.addWidget(self.timeout_spin)
        extra_opts_layout.addStretch()

        config_layout.addLayout(extra_opts_layout)
        main_layout.addWidget(config_group)

        # === Botões de Ação ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.scan_btn = QPushButton("Iniciar Scan")
        self.scan_btn.setObjectName("scanButton")
        self.scan_btn.setMinimumHeight(36)
        self.scan_btn.clicked.connect(self.start_scan)

        self.stop_btn = QPushButton("Interromper")
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

        # Barra de Progresso indeterminada
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # === Área de Resultado ===
        output_group = QGroupBox("Resultado do Scan (Tempo Real)")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        # Fonte monoespaçada para saída do terminal
        mono_font = QFont("Monospace")
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        mono_font.setPointSize(10)
        self.output_text.setFont(mono_font)
        output_layout.addWidget(self.output_text)

        main_layout.addWidget(output_group)

        self.statusBar().showMessage("Pronto")

    def apply_theme(self, theme_name: str):
        """Aplica a folha de estilo do tema selecionado."""
        style = get_theme_stylesheet(theme_name)
        QApplication.instance().setStyleSheet(style)
        self.settings.setValue("theme", theme_name)
        self.setWindowTitle(f"Nmap GUI — {theme_name}")

    def _load_saved_settings(self):
        """Carrega preferências salvas do usuário."""
        saved_theme = self.settings.value("theme", "Padrão")
        if saved_theme in get_theme_names():
            self.theme_combo.setCurrentText(saved_theme)
            self.apply_theme(saved_theme)
        else:
            self.apply_theme("Padrão")

    def _check_nmap_status(self):
        """Exibe a versão do Nmap na barra de status."""
        if not self.logic.is_available():
            self.statusBar().showMessage("Aviso: Nmap não encontrado no PATH do sistema!")
            return
        try:
            version = self.logic.get_version()
            self.statusBar().showMessage(f"Nmap detectado: {version}")
        except NmapError as e:
            self.statusBar().showMessage(str(e))

    def start_scan(self):
        """Inicia a execução do scan em thread separada com streaming."""
        target = self.target_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Alvo Necessário", "Por favor, especifique um alvo (IP ou hostname).")
            self.target_edit.setFocus()
            return

        if not self.logic.is_available():
            QMessageBox.critical(
                self,
                "Nmap Não Encontrado",
                "O executável 'nmap' não foi encontrado no PATH do sistema.\n"
                "Por favor, instale o Nmap para utilizar esta ferramenta."
            )
            return

        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Aguarde", "Já existe um scan em andamento.")
            return

        ports = self.ports_edit.text().strip()
        scan_type = self.scan_type_combo.currentData()
        timing = self.timing_combo.currentText()
        extra = self.extra_edit.text().strip()
        output_format = "xml" if self.xml_checkbox.isChecked() else "normal"

        self.output_text.clear()
        self.output_text.append(">>> Iniciando varredura com Nmap...\n")
        cmd_preview = f"nmap {scan_type} -{timing} " + (f"-p {ports} " if ports else "") + f"{extra} {target}"
        self.output_text.append(f"> Comando: {cmd_preview}\n")
        self.output_text.append("=" * 65 + "\n\n")

        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setVisible(True)
        self.statusBar().showMessage(f"Varrendo alvo: {target}...")

        self.worker = ScanWorker(
            self.logic,
            target=target,
            ports=ports,
            scan_type=scan_type,
            extra_args=extra,
            timing=timing,
            output_format=output_format
        )
        self.worker.line_received.connect(self._on_line_received)
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.error.connect(self._on_scan_error)
        self.worker.start()

    def _on_line_received(self, line: str):
        """Insere cada linha recebida no QTextEdit com autoscroll."""
        self.output_text.insertPlainText(line)
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)

    def stop_scan(self):
        """Interrompe a varredura em andamento."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)
            self.output_text.append("\n\n>>> [AVISO] Scan interrompido pelo usuário.\n")
            self._reset_ui()
            self.statusBar().showMessage("Scan interrompido pelo usuário.")

    def _on_scan_finished(self, returncode: int):
        self.output_text.append(f"\n\n>>> Scan finalizado com código de retorno: {returncode}\n")
        self._reset_ui()
        self.statusBar().showMessage(f"Scan finalizado com sucesso (código {returncode}).")

    def _on_scan_error(self, message: str):
        self.output_text.append(f"\n\n[ERRO FATAL] {message}\n")
        QMessageBox.critical(self, "Erro na Execução", message)
        self._reset_ui()
        self.statusBar().showMessage("Erro durante a execução do scan.")

    def _reset_ui(self):
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)

    def clear_output(self):
        self.output_text.clear()

    def save_output_to_file(self):
        """Exporta o conteúdo atual da área de saída para um arquivo."""
        text = self.output_text.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "Vazio", "Não há resultados para exportar.")
            return

        is_xml = self.xml_checkbox.isChecked()
        default_filter = "Arquivos XML (*.xml)" if is_xml else "Arquivos de Texto (*.txt)"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Resultado do Scan",
            "nmap_scan.xml" if is_xml else "nmap_scan.txt",
            "Arquivos de Texto (*.txt);;Arquivos XML (*.xml);;Todos os Arquivos (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                QMessageBox.information(self, "Sucesso", f"Resultado salvo em:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = NmapGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
