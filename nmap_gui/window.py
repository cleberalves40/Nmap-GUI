"""
Interface gráfica PyQt6 para o Nmap Scanner.
Suporte a temas dinâmicos (Padrão, Charcoal, Selenized, Catppuccin) e streaming de saída em tempo real.
"""

import sys
import os
import json
import shlex
import subprocess
import threading
import time
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QStandardPaths
from PyQt6.QtGui import QFont, QTextCursor, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QProgressBar, QCheckBox, QSpinBox,
    QFileDialog, QStatusBar, QTabWidget, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QAbstractItemView, QInputDialog
)

from .logic import (
    NmapHistoryStore, NmapLogic, NmapError, ScanProfileStore,
    is_nmap_version_outdated, latest_stable_nmap_tag,
    compare_nmap_xml, parse_nmap_xml,
)
from .themes import THEMES, STYLE_PADRAO, get_theme_names, get_theme_stylesheet


class ScanWorker(QThread):
    """
    Worker thread que executa o Nmap via subprocess.Popen
    e envia linhas de saída em tempo real para a interface gráfica.
    """
    line_received = pyqtSignal(str)
    scan_finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, logic: NmapLogic, **kwargs):
        super().__init__()
        self.logic = logic
        self.kwargs = kwargs
        self.timeout = kwargs.pop("timeout", None)
        self.output_format = kwargs.get("output_format", "normal")
        self.process = None
        self._is_stopped = False
        self._stdout_chunks = []
        self._xml_output = None

    @property
    def xml_output(self):
        return self._xml_output

    @property
    def scan_output(self):
        return "".join(self._stdout_chunks)

    def _read_stream(self, stream, is_stdout):
        for line in iter(stream.readline, ""):
            if is_stdout:
                self._stdout_chunks.append(line)
                self.line_received.emit(line)
            else:
                self.line_received.emit(f"[STDERR] {line}")
        stream.close()

    def _terminate_process(self):
        if not self.process or self.process.poll() is not None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        except OSError:
            if self.process.poll() is None:
                raise

    def run(self):
        try:
            self.process = self.logic.create_process(**self.kwargs)
            readers = [
                threading.Thread(target=self._read_stream, args=(self.process.stdout, True)),
                threading.Thread(target=self._read_stream, args=(self.process.stderr, False)),
            ]
            for reader in readers:
                reader.start()

            started_at = time.monotonic()
            timed_out = False
            while self.process.poll() is None:
                if self._is_stopped:
                    self._terminate_process()
                    break
                if self.timeout and time.monotonic() - started_at >= self.timeout:
                    timed_out = True
                    self._terminate_process()
                    break
                self.msleep(50)

            returncode = self.process.wait()
            for reader in readers:
                reader.join()

            if timed_out:
                self.error.emit("O scan excedeu o tempo limite definido.")
                return
            if self.output_format == "xml":
                raw_xml = "".join(self._stdout_chunks)
                try:
                    root = ET.fromstring(raw_xml)
                except ET.ParseError:
                    pass
                else:
                    if root.tag == "nmaprun":
                        self._xml_output = raw_xml
            if not self._is_stopped:
                self.scan_finished.emit(returncode)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Interrompe o processo do Nmap de forma limpa."""
        self._is_stopped = True
        self._terminate_process()


class NmapVersionCheckWorker(QThread):
    checked = pyqtSignal(str, str)
    TAGS_URL = "https://api.github.com/repos/nmap/nmap/tags?per_page=100"

    def run(self):
        try:
            request = Request(
                self.TAGS_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Nmap-GUI",
                },
            )
            with urlopen(request, timeout=6) as response:
                tags = json.load(response)
            self.checked.emit(latest_stable_nmap_tag(tags), "")
        except Exception as e:
            self.checked.emit("", str(e))


class NmapGUI(QMainWindow):
    """Janela principal da aplicação Nmap GUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nmap GUI")
        self.setMinimumSize(940, 680)
        self.resize(1040, 740)

        self.logic = NmapLogic()
        self.worker: Optional[ScanWorker] = None
        self.last_output_format = "normal"
        self.last_xml_output = None
        self.last_scan_output = ""
        self.current_scan_target = ""
        self.last_command_preview = ""
        self.settings = QSettings("NmapGUI", "NmapApp")
        app_data = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        self.history_store = NmapHistoryStore(
            app_data or str(Path.home() / ".local" / "share" / "nmap-gui")
        )
        self.profile_store = ScanProfileStore(
            app_data or str(Path.home() / ".local" / "share" / "nmap-gui")
        )
        self._result_rows = []
        self._history_records = []
        self.installed_nmap_version = ""
        self.version_check_worker: Optional[NmapVersionCheckWorker] = None

        self._build_ui()
        self._load_saved_settings()
        self._check_nmap_status()

    def closeEvent(self, event):
        worker = self.version_check_worker
        if worker and worker.isRunning() and not worker.wait(7000):
            self.statusBar().showMessage("Aguarde a conclusão da consulta de versão.")
            event.ignore()
            return
        super().closeEvent(event)

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

        self.version_check_button = QPushButton("Verificar versão do Nmap")
        self.version_check_button.clicked.connect(self.check_nmap_updates)
        top_bar.addWidget(self.version_check_button)

        main_layout.addLayout(top_bar)

        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Perfil:"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(220)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        profile_row.addWidget(self.profile_combo)
        self.save_profile_button = QPushButton("Salvar perfil...")
        self.save_profile_button.clicked.connect(self.save_scan_profile)
        profile_row.addWidget(self.save_profile_button)
        self.delete_profile_button = QPushButton("Excluir perfil")
        self.delete_profile_button.setEnabled(False)
        self.delete_profile_button.clicked.connect(self.delete_scan_profile)
        profile_row.addWidget(self.delete_profile_button)
        profile_row.addStretch()
        main_layout.addLayout(profile_row)

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

        target_file_layout = QHBoxLayout()
        target_file_layout.addWidget(QLabel("Arquivo de alvos:"))
        self.target_file_edit = QLineEdit()
        self.target_file_edit.setPlaceholderText("Opcional: lista de hosts (-iL)")
        target_file_layout.addWidget(self.target_file_edit, 1)
        self.browse_targets_button = QPushButton("Selecionar...")
        self.browse_targets_button.clicked.connect(self.select_target_file)
        target_file_layout.addWidget(self.browse_targets_button)
        config_layout.addLayout(target_file_layout)

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

        self.ipv6_checkbox = QCheckBox("IPv6 (-6)")
        opts_layout.addWidget(self.ipv6_checkbox)

        config_layout.addLayout(opts_layout)

        advanced_scan_layout = QHBoxLayout()
        self.top_ports_checkbox = QCheckBox("Top ports:")
        advanced_scan_layout.addWidget(self.top_ports_checkbox)
        self.top_ports_spin = QSpinBox()
        self.top_ports_spin.setRange(1, 65535)
        self.top_ports_spin.setValue(1000)
        self.top_ports_spin.setEnabled(False)
        self.top_ports_checkbox.toggled.connect(self.top_ports_spin.setEnabled)
        advanced_scan_layout.addWidget(self.top_ports_spin)

        self.version_intensity_checkbox = QCheckBox("Intensidade -sV:")
        advanced_scan_layout.addWidget(self.version_intensity_checkbox)
        self.version_intensity_spin = QSpinBox()
        self.version_intensity_spin.setRange(0, 9)
        self.version_intensity_spin.setValue(7)
        self.version_intensity_spin.setEnabled(False)
        self.version_intensity_checkbox.toggled.connect(self.version_intensity_spin.setEnabled)
        advanced_scan_layout.addWidget(self.version_intensity_spin)
        advanced_scan_layout.addStretch()
        config_layout.addLayout(advanced_scan_layout)

        exclude_layout = QHBoxLayout()
        exclude_layout.addWidget(QLabel("Excluir alvos:"))
        self.exclude_edit = QLineEdit()
        self.exclude_edit.setPlaceholderText("Ex: 192.0.2.5,192.0.2.0/28")
        exclude_layout.addWidget(self.exclude_edit)
        config_layout.addLayout(exclude_layout)

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

        self.output_tabs = QTabWidget()

        # === Terminal ===
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
        self.output_tabs.addTab(output_group, "Terminal")

        # === Resultados estruturados ===
        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)
        self.results_filter = QLineEdit()
        self.results_filter.setPlaceholderText("Filtrar host, porta, estado ou serviço")
        self.results_filter.textChanged.connect(self._filter_results)
        results_layout.addWidget(self.results_filter)
        self.results_table = QTableWidget(0, 10)
        self.results_table.setHorizontalHeaderLabels([
            "Host", "Nome", "Host", "Porta", "Proto", "Estado",
            "Serviço", "Produto", "Versão", "Scripts",
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_table)
        self.output_tabs.addTab(results_page, "Resultados")

        # === Histórico e comparação ===
        history_page = QWidget()
        history_layout = QVBoxLayout(history_page)
        history_actions = QHBoxLayout()
        self.open_history_button = QPushButton("Abrir selecionado")
        self.open_history_button.clicked.connect(self.open_selected_scan)
        self.compare_history_button = QPushButton("Comparar dois XMLs")
        self.compare_history_button.clicked.connect(self.compare_selected_scans)
        history_actions.addWidget(self.open_history_button)
        history_actions.addWidget(self.compare_history_button)
        history_actions.addStretch()
        history_layout.addLayout(history_actions)
        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        history_layout.addWidget(self.history_list, 1)
        self.comparison_table = QTableWidget(0, 6)
        self.comparison_table.setHorizontalHeaderLabels([
            "Mudança", "Host", "Proto", "Porta", "Anterior", "Atual",
        ])
        self.comparison_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.comparison_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.comparison_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.comparison_table, 1)
        self.output_tabs.addTab(history_page, "Histórico")

        main_layout.addWidget(self.output_tabs, 1)
        self._refresh_history()
        self._refresh_profiles()

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
            self.installed_nmap_version = ""
            self.statusBar().showMessage("Aviso: Nmap não encontrado no PATH do sistema!")
            return
        try:
            self.installed_nmap_version = self.logic.get_version()
            self.statusBar().showMessage(f"Nmap detectado: {self.installed_nmap_version}")
        except NmapError as e:
            self.installed_nmap_version = ""
            self.statusBar().showMessage(str(e))

    def check_nmap_updates(self):
        if self.version_check_worker and self.version_check_worker.isRunning():
            return
        self.version_check_button.setEnabled(False)
        self.statusBar().showMessage("Consultando versão estável do Nmap...")
        self.version_check_worker = NmapVersionCheckWorker(self)
        self.version_check_worker.checked.connect(self._on_nmap_version_checked)
        self.version_check_worker.finished.connect(self._release_version_check_worker)
        self.version_check_worker.start()

    def _release_version_check_worker(self):
        if self.version_check_worker and not self.version_check_worker.isRunning():
            self.version_check_worker = None

    def _on_nmap_version_checked(self, latest_version, error):
        self.version_check_button.setEnabled(True)
        if error:
            self.statusBar().showMessage(f"Não foi possível consultar o Nmap upstream: {error}", 15000)
            return
        if not self.installed_nmap_version:
            QMessageBox.information(
                self, "Versão do Nmap",
                f"Última versão estável upstream: {latest_version}.\n\n"
                "O Nmap não foi encontrado localmente. Instale-o manualmente em "
                "https://nmap.org/download.html.",
            )
            return
        try:
            outdated = is_nmap_version_outdated(
                self.installed_nmap_version, latest_version
            )
        except NmapError as e:
            self.statusBar().showMessage(str(e), 15000)
            return
        if outdated:
            message = (
                f"Versão instalada: {self.installed_nmap_version}\n"
                f"Última versão estável: Nmap {latest_version}\n\n"
                "Baixe a atualização manualmente em https://nmap.org/download.html. "
                "Nenhuma atualização foi instalada."
            )
        else:
            message = (
                f"Versão instalada: {self.installed_nmap_version}\n"
                f"Última versão estável: Nmap {latest_version}\n\n"
                "O Nmap instalado está atualizado ou é mais recente."
            )
        QMessageBox.information(self, "Versão do Nmap", message)

    def start_scan(self):
        """Inicia a execução do scan em thread separada com streaming."""
        target = self.target_edit.text().strip()
        input_file = self.target_file_edit.text().strip()
        if bool(target) == bool(input_file):
            QMessageBox.warning(
                self, "Alvo Necessário",
                "Informe um alvo ou selecione um arquivo de alvos.",
            )
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

        scan_type = self.scan_type_combo.currentData()
        if (self.version_intensity_checkbox.isChecked()
                and scan_type not in ("-sV", "-A")):
            QMessageBox.warning(
                self, "Opção incompatível",
                "A intensidade de versão requer o perfil -sV ou -A.",
            )
            return

        ports = self.ports_edit.text().strip()
        timing = self.timing_combo.currentText()
        extra = self.extra_edit.text().strip()
        output_format = "xml" if self.xml_checkbox.isChecked() else "normal"
        options = {
            "target": target,
            "input_file": input_file or None,
            "ports": ports,
            "scan_type": scan_type,
            "extra_args": extra,
            "timing": timing,
            "output_format": output_format,
            "exclude_targets": self.exclude_edit.text().strip(),
            "ipv6": self.ipv6_checkbox.isChecked(),
            "top_ports": (
                self.top_ports_spin.value() if self.top_ports_checkbox.isChecked() else None
            ),
            "version_intensity": (
                self.version_intensity_spin.value()
                if self.version_intensity_checkbox.isChecked() else None
            ),
        }
        try:
            command = self.logic.build_command(**options)
        except NmapError as e:
            QMessageBox.warning(self, "Opções inválidas", str(e))
            return

        self.last_output_format = output_format
        self.last_xml_output = None
        self.last_scan_output = ""
        self.current_scan_target = target or f"Lista: {input_file}"
        self._populate_results([])

        self.output_text.clear()
        self.output_text.append(">>> Iniciando varredura com Nmap...\n")
        cmd_preview = shlex.join(command)
        self.last_command_preview = cmd_preview
        self.output_text.append(f"> Comando: {cmd_preview}\n")
        self.output_text.append("=" * 65 + "\n\n")

        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setVisible(True)
        scan_label = target or f"arquivo {input_file}"
        self.statusBar().showMessage(f"Varrendo: {scan_label}...")

        self.worker = ScanWorker(
            self.logic,
            **options,
            timeout=self.timeout_spin.value() or None
        )
        self.worker.line_received.connect(self._on_line_received)
        self.worker.scan_finished.connect(self._on_scan_finished)
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
        self.last_scan_output = self.worker.scan_output if self.worker else ""
        if self.last_output_format == "xml" and self.worker:
            self.last_xml_output = self.worker.xml_output
            if self.last_xml_output:
                try:
                    self._populate_results(parse_nmap_xml(self.last_xml_output))
                    self.output_tabs.setCurrentIndex(1)
                except NmapError as e:
                    self.statusBar().showMessage(str(e))

        saved_format = "xml" if self.last_xml_output else "text"
        saved_output = self.last_xml_output or self.last_scan_output
        if saved_output:
            try:
                self.history_store.save_scan(
                    target=self.current_scan_target,
                    output_format=saved_format,
                    content=saved_output,
                    returncode=returncode,
                    command=self.last_command_preview,
                )
                self._refresh_history()
            except (NmapError, OSError) as e:
                self.statusBar().showMessage(f"Scan concluído; histórico não salvo: {e}")

        self.output_text.append(f"\n\n>>> Scan finalizado com código de retorno: {returncode}\n")
        self._reset_ui()
        self.statusBar().showMessage(
            f"Scan finalizado com código de retorno {returncode}."
        )

    def _on_scan_error(self, message: str):
        self.output_text.append(f"\n\n[ERRO FATAL] {message}\n")
        QMessageBox.critical(self, "Erro na Execução", message)
        self._reset_ui()
        self.statusBar().showMessage("Erro durante a execução do scan.")

    def _populate_results(self, rows):
        self._result_rows = rows
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(len(rows))
        fields = (
            "host", "hostname", "host_status", "port", "protocol", "state",
            "service", "product", "version", "scripts",
        )
        for row_index, result in enumerate(rows):
            for column_index, field in enumerate(fields):
                self.results_table.setItem(
                    row_index, column_index,
                    QTableWidgetItem(result.get(field, "")),
                )
        self.results_table.setSortingEnabled(True)
        self._filter_results(self.results_filter.text())

    def _filter_results(self, text):
        needle = text.casefold().strip()
        for row_index in range(self.results_table.rowCount()):
            values = [
                self.results_table.item(row_index, column).text()
                for column in range(self.results_table.columnCount())
                if self.results_table.item(row_index, column)
            ]
            self.results_table.setRowHidden(
                row_index, bool(needle) and needle not in " ".join(values).casefold()
            )

    def _refresh_history(self):
        try:
            self._history_records = self.history_store.list_scans()
        except NmapError as e:
            self.statusBar().showMessage(str(e))
            self._history_records = []
        self.history_list.clear()
        for record in self._history_records:
            timestamp = record.get("timestamp", "").replace("T", " ").replace("+00:00", " UTC")
            label = (
                f"{timestamp} | {record.get('target', '')} | "
                f"{record.get('format', 'text').upper()} | exit {record.get('returncode', '?')}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, record.get("id"))
            self.history_list.addItem(item)

    def open_selected_scan(self):
        selected = self.history_list.selectedItems()
        if len(selected) != 1:
            QMessageBox.information(self, "Histórico", "Selecione uma execução.")
            return
        try:
            record, content = self.history_store.load_scan(
                selected[0].data(Qt.ItemDataRole.UserRole)
            )
        except NmapError as e:
            QMessageBox.warning(self, "Histórico", str(e))
            return
        self.last_output_format = "xml" if record["format"] == "xml" else "normal"
        self.last_scan_output = content
        self.last_xml_output = content if self.last_output_format == "xml" else None
        if self.last_xml_output:
            try:
                self._populate_results(parse_nmap_xml(content))
            except NmapError as e:
                QMessageBox.warning(self, "Histórico", str(e))
                return
            self.output_tabs.setCurrentIndex(1)
        else:
            self.output_text.setPlainText(content)
            self.output_tabs.setCurrentIndex(0)

    def compare_selected_scans(self):
        selected = self.history_list.selectedItems()
        if len(selected) != 2:
            QMessageBox.information(self, "Comparação", "Selecione exatamente dois XMLs.")
            return
        records = []
        try:
            for item in selected:
                record, content = self.history_store.load_scan(
                    item.data(Qt.ItemDataRole.UserRole)
                )
                if record["format"] != "xml":
                    raise NmapError("A comparação só funciona entre resultados XML.")
                records.append((record, content))
            records.sort(key=lambda entry: entry[0].get("timestamp", ""))
            changes = compare_nmap_xml(records[0][1], records[1][1])
        except NmapError as e:
            QMessageBox.warning(self, "Comparação", str(e))
            return

        self.comparison_table.setRowCount(max(1, len(changes)))
        if not changes:
            self.comparison_table.setItem(0, 0, QTableWidgetItem("Sem diferenças"))
        else:
            fields = ("change", "host", "protocol", "port", "before", "after")
            for row_index, change in enumerate(changes):
                for column_index, field in enumerate(fields):
                    self.comparison_table.setItem(
                        row_index, column_index,
                        QTableWidgetItem(change.get(field, "")),
                    )
        self.output_tabs.setCurrentIndex(2)

    def select_target_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar lista de alvos",
            "",
            "Listas de texto (*.txt);;Todos os arquivos (*)",
        )
        if file_path:
            self.target_file_edit.setText(file_path)
            self.target_edit.clear()

    def _profile_options(self):
        return {
            "target": self.target_edit.text(),
            "input_file": self.target_file_edit.text(),
            "ports": self.ports_edit.text(),
            "scan_type": self.scan_type_combo.currentData(),
            "timing": self.timing_combo.currentText(),
            "extra_args": self.extra_edit.text(),
            "exclude_targets": self.exclude_edit.text(),
            "ipv6": self.ipv6_checkbox.isChecked(),
            "top_ports_enabled": self.top_ports_checkbox.isChecked(),
            "top_ports": self.top_ports_spin.value(),
            "version_intensity_enabled": self.version_intensity_checkbox.isChecked(),
            "version_intensity": self.version_intensity_spin.value(),
            "output_format": "xml" if self.xml_checkbox.isChecked() else "normal",
            "timeout": self.timeout_spin.value(),
        }

    def _refresh_profiles(self, selected_name=None):
        try:
            profiles = self.profile_store.list_profiles()
        except NmapError as e:
            self.statusBar().showMessage(str(e))
            profiles = {}
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("Selecionar perfil...", None)
        for name in sorted(profiles, key=str.casefold):
            self.profile_combo.addItem(name, name)
        if selected_name:
            index = self.profile_combo.findData(selected_name)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
        self.profile_combo.blockSignals(False)
        self.delete_profile_button.setEnabled(self.profile_combo.currentData() is not None)

    def _on_profile_selected(self, _index):
        profile_name = self.profile_combo.currentData()
        self.delete_profile_button.setEnabled(profile_name is not None)
        if profile_name is None:
            return
        try:
            profile = self.profile_store.list_profiles().get(profile_name)
        except NmapError as e:
            QMessageBox.warning(self, "Perfil", str(e))
            return
        if profile is None:
            return

        self.target_edit.setText(profile.get("target", ""))
        self.target_file_edit.setText(profile.get("input_file", ""))
        self.ports_edit.setText(profile.get("ports", ""))
        scan_index = self.scan_type_combo.findData(profile.get("scan_type"))
        if scan_index >= 0:
            self.scan_type_combo.setCurrentIndex(scan_index)
        timing_index = self.timing_combo.findText(profile.get("timing", "T3"))
        if timing_index >= 0:
            self.timing_combo.setCurrentIndex(timing_index)
        self.extra_edit.setText(profile.get("extra_args", ""))
        self.exclude_edit.setText(profile.get("exclude_targets", ""))
        self.ipv6_checkbox.setChecked(bool(profile.get("ipv6", False)))
        self.top_ports_checkbox.setChecked(bool(profile.get("top_ports_enabled", False)))
        self.top_ports_spin.setValue(int(profile.get("top_ports", 1000)))
        self.version_intensity_checkbox.setChecked(
            bool(profile.get("version_intensity_enabled", False))
        )
        self.version_intensity_spin.setValue(int(profile.get("version_intensity", 7)))
        self.xml_checkbox.setChecked(profile.get("output_format") == "xml")
        self.timeout_spin.setValue(int(profile.get("timeout", 0)))

    def save_scan_profile(self):
        name, accepted = QInputDialog.getText(self, "Salvar perfil", "Nome do perfil:")
        if not accepted:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Perfil", "Informe um nome para o perfil.")
            return
        try:
            profiles = self.profile_store.list_profiles()
            if name in profiles:
                answer = QMessageBox.question(
                    self, "Sobrescrever perfil",
                    f'O perfil "{name}" já existe. Deseja substituí-lo?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
            self.profile_store.save_profile(name, self._profile_options())
        except NmapError as e:
            QMessageBox.warning(self, "Perfil", str(e))
            return
        self._refresh_profiles(name)
        self.statusBar().showMessage(f'Perfil "{name}" salvo.')

    def delete_scan_profile(self):
        name = self.profile_combo.currentData()
        if name is None:
            return
        answer = QMessageBox.question(
            self, "Excluir perfil", f'Deseja excluir o perfil "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.profile_store.delete_profile(name)
        except NmapError as e:
            QMessageBox.warning(self, "Perfil", str(e))
            return
        self._refresh_profiles()
        self.statusBar().showMessage(f'Perfil "{name}" excluído.')

    def _reset_ui(self):
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)

    def clear_output(self):
        self.output_text.clear()

    def save_output_to_file(self):
        """Exporta o conteúdo atual da área de saída para um arquivo."""
        is_xml = self.last_output_format == "xml"
        if is_xml:
            text = self.last_xml_output
            if text is None:
                QMessageBox.information(
                    self, "XML indisponível",
                    "Não há uma saída XML íntegra para exportar."
                )
                return
        else:
            text = self.last_scan_output
        if not text.strip():
            QMessageBox.information(self, "Vazio", "Não há resultados para exportar.")
            return

        default_filter = "Arquivos XML (*.xml)" if is_xml else "Arquivos de Texto (*.txt)"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Resultado do Scan",
            "nmap_scan.xml" if is_xml else "nmap_scan.txt",
            f"{default_filter};;Todos os Arquivos (*)"
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
