"""
Módulo de lógica de comandos do Nmap.
Responsável por construir e executar comandos nmap de forma segura.
"""

import json
import os
import re
import shutil
import shlex
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict


class NmapError(Exception):
    """Exceção personalizada para erros relacionados ao Nmap."""
    pass


_NMAP_VERSION_PATTERN = re.compile(r"(?<!\d)(\d+(?:\.\d+)+)(?!\d)")
_STABLE_NMAP_TAG_PATTERN = re.compile(r"v?(\d+(?:\.\d+)+)")


def parse_nmap_version(version_text):
    """Return numeric components from an Nmap version string or tag."""
    match = _NMAP_VERSION_PATTERN.search(version_text)
    if not match:
        raise NmapError(f"Versão do Nmap inválida: {version_text}")
    return tuple(int(component) for component in match.group(1).split("."))


def latest_stable_nmap_tag(tags):
    """Select the newest stable numeric version from upstream tag names."""
    versions = []
    for tag in tags:
        name = tag.get("name", "") if isinstance(tag, dict) else ""
        match = _STABLE_NMAP_TAG_PATTERN.fullmatch(name)
        if match:
            version = match.group(1)
            versions.append((parse_nmap_version(version), version))
    if not versions:
        raise NmapError("A consulta não retornou tags estáveis do Nmap.")
    return max(versions, key=lambda item: item[0])[1]


def is_nmap_version_outdated(installed, latest):
    return parse_nmap_version(installed) < parse_nmap_version(latest)


def parse_nmap_xml(xml_data: str) -> List[Dict[str, str]]:
    """Convert Nmap XML into one display-ready row per host and port."""
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise NmapError(f"XML do Nmap inválido: {e}") from e
    if root.tag != "nmaprun":
        raise NmapError("O documento não contém uma raiz <nmaprun>.")

    rows = []
    for host in root.findall("host"):
        addresses = host.findall("address")
        address = next(
            (item.get("addr", "") for item in addresses
             if item.get("addrtype") in ("ipv4", "ipv6")),
            addresses[0].get("addr", "") if addresses else "",
        )
        hostname_node = host.find("./hostnames/hostname")
        hostname = hostname_node.get("name", "") if hostname_node is not None else ""
        host_status_node = host.find("status")
        host_status = host_status_node.get("state", "unknown") if host_status_node is not None else "unknown"
        ports = host.findall("./ports/port")

        if not ports:
            rows.append({
                "host": address,
                "hostname": hostname,
                "host_status": host_status,
                "port": "",
                "protocol": "",
                "state": "",
                "service": "",
                "product": "",
                "version": "",
                "extra_info": "",
                "scripts": "",
            })
            continue

        for port in ports:
            state_node = port.find("state")
            service_node = port.find("service")
            scripts = [
                f"{script.get('id', '')}: {script.get('output', '')}"
                for script in port.findall("script")
            ]
            rows.append({
                "host": address,
                "hostname": hostname,
                "host_status": host_status,
                "port": port.get("portid", ""),
                "protocol": port.get("protocol", ""),
                "state": state_node.get("state", "") if state_node is not None else "",
                "service": service_node.get("name", "") if service_node is not None else "",
                "product": service_node.get("product", "") if service_node is not None else "",
                "version": service_node.get("version", "") if service_node is not None else "",
                "extra_info": service_node.get("extrainfo", "") if service_node is not None else "",
                "scripts": "\n".join(scripts),
            })
    return rows


def compare_nmap_xml(previous_xml: str, current_xml: str) -> List[Dict[str, str]]:
    """Summarize host and port changes between two Nmap XML documents."""
    previous_rows = parse_nmap_xml(previous_xml)
    current_rows = parse_nmap_xml(current_xml)

    previous_hosts = {row["host"]: row["host_status"] for row in previous_rows}
    current_hosts = {row["host"]: row["host_status"] for row in current_rows}
    changes = []
    for host in sorted(set(previous_hosts) | set(current_hosts)):
        before = previous_hosts.get(host, "")
        after = current_hosts.get(host, "")
        if before != after:
            changes.append({
                "change": "Host adicionado" if not before else "Host removido" if not after else "Estado do host alterado",
                "host": host,
                "protocol": "",
                "port": "",
                "before": before,
                "after": after,
            })

    def port_map(rows):
        return {
            (row["host"], row["protocol"], row["port"]): row
            for row in rows if row["port"]
        }

    previous_ports = port_map(previous_rows)
    current_ports = port_map(current_rows)
    for key in sorted(set(previous_ports) | set(current_ports)):
        before = previous_ports.get(key)
        after = current_ports.get(key)
        if before is None:
            change = "Porta adicionada"
        elif after is None:
            change = "Porta removida"
        elif any(before[field] != after[field] for field in
                 ("state", "service", "product", "version", "extra_info", "scripts")):
            change = "Porta alterada"
        else:
            continue

        def describe(row):
            if row is None:
                return ""
            service = " ".join(filter(None, (row["service"], row["product"], row["version"])))
            return " | ".join(filter(None, (row["state"], service, row["scripts"])))

        changes.append({
            "change": change,
            "host": key[0],
            "protocol": key[1],
            "port": key[2],
            "before": describe(before),
            "after": describe(after),
        })
    return changes


class NmapHistoryStore:
    """Persist scan artifacts and a searchable JSON manifest in app data."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.results_directory = self.directory / "results"
        self.manifest_path = self.directory / "history.json"

    def list_scans(self) -> List[Dict[str, str]]:
        if not self.manifest_path.exists():
            return []
        try:
            records = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise NmapError(f"Não foi possível ler o histórico: {e}") from e
        if not isinstance(records, list):
            raise NmapError("O índice do histórico está em formato inválido.")
        return sorted(records, key=lambda item: item.get("timestamp", ""), reverse=True)

    def save_scan(self, target, output_format, content, returncode, command=""):
        if not content:
            return None
        self.results_directory.mkdir(parents=True, exist_ok=True)
        scan_id = uuid.uuid4().hex
        filename = f"{scan_id}.xml" if output_format == "xml" else f"{scan_id}.txt"
        (self.results_directory / filename).write_text(content, encoding="utf-8")
        record = {
            "id": scan_id,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "target": target,
            "format": output_format,
            "returncode": int(returncode),
            "command": command,
            "filename": filename,
        }
        records = self.list_scans()
        records.insert(0, record)
        self.directory.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.directory,
                delete=False, prefix="history-", suffix=".tmp"
            ) as temp_file:
                json.dump(records, temp_file, ensure_ascii=False, indent=2)
                temp_path = temp_file.name
            os.replace(temp_path, self.manifest_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        return record

    def load_scan(self, scan_id):
        record = next((item for item in self.list_scans() if item.get("id") == scan_id), None)
        if record is None:
            raise NmapError("A execução selecionada não está mais no histórico.")
        if record.get("format") not in ("xml", "text"):
            raise NmapError("O formato do resultado salvo é inválido.")
        filename = f"{scan_id}.xml" if record["format"] == "xml" else f"{scan_id}.txt"
        try:
            content = (self.results_directory / filename).read_text(encoding="utf-8")
        except OSError as e:
            raise NmapError(f"Não foi possível ler o resultado salvo: {e}") from e
        return record, content


class ScanProfileStore:
    """Persist named scan configurations as a JSON object."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.profiles_path = self.directory / "profiles.json"

    def list_profiles(self):
        if not self.profiles_path.exists():
            return {}
        try:
            profiles = json.loads(self.profiles_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise NmapError(f"Não foi possível ler os perfis: {e}") from e
        if not isinstance(profiles, dict) or any(
            not isinstance(name, str) or not isinstance(value, dict)
            for name, value in profiles.items()
        ):
            raise NmapError("O arquivo de perfis está em formato inválido.")
        return profiles

    def save_profile(self, name, options):
        name = name.strip()
        if not name:
            raise NmapError("O nome do perfil não pode estar vazio.")
        if not isinstance(options, dict):
            raise NmapError("As opções do perfil estão em formato inválido.")
        profiles = self.list_profiles()
        profiles[name] = options
        self._write_profiles(profiles)

    def delete_profile(self, name):
        profiles = self.list_profiles()
        if name not in profiles:
            return
        del profiles[name]
        self._write_profiles(profiles)

    def _write_profiles(self, profiles):
        self.directory.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.directory,
                delete=False, prefix="profiles-", suffix=".tmp"
            ) as temp_file:
                json.dump(profiles, temp_file, ensure_ascii=False, indent=2)
                temp_path = temp_file.name
            os.replace(temp_path, self.profiles_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)


class NmapLogic:
    """Classe que encapsula a lógica de execução e comando do Nmap."""

    def __init__(self):
        self.nmap_path = self._find_nmap()

    def _find_nmap(self) -> Optional[str]:
        """Procura o executável do nmap no PATH."""
        return shutil.which("nmap")

    def is_available(self) -> bool:
        """Verifica se o Nmap está instalado e disponível."""
        return bool(self.nmap_path)

    def get_version(self) -> str:
        """Retorna a versão do Nmap instalado."""
        if not self.nmap_path:
            raise NmapError(
                "Nmap não encontrado no PATH do sistema.\n"
                "Instale o Nmap e certifique-se de que ele está acessível."
            )
        try:
            result = subprocess.run(
                [self.nmap_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            first_line = result.stdout.splitlines()[0] if result.stdout else "Desconhecida"
            return first_line.strip()
        except Exception as e:
            raise NmapError(f"Não foi possível obter a versão do Nmap: {e}")

    def build_command(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "-sS",
        extra_args: str = "",
        timing: str = "T3",
        output_format: str = "normal",
        input_file: Optional[str] = None,
        exclude_targets: str = "",
        ipv6: bool = False,
        top_ports: Optional[int] = None,
        version_intensity: Optional[int] = None,
    ) -> List[str]:
        """
        Constrói a lista de argumentos do comando nmap.

        Args:
            target: Alvo (IP, hostname ou faixa CIDR)
            ports: Portas (ex: "22,80,443" ou "1-1000")
            scan_type: Tipo de scan (ex: -sS, -sT, -sV, -sU, -A)
            extra_args: Argumentos adicionais livres
            timing: Perfil de tempo (T0 a T5)
            output_format: "normal" ou "xml"

        Returns:
            Lista de argumentos para subprocess
        """
        has_target = bool(target and target.strip())
        has_input_file = bool(input_file and input_file.strip())
        if has_target == has_input_file:
            raise NmapError("Informe um alvo ou um arquivo de alvos, mas não ambos.")
        if has_input_file and not Path(input_file).is_file():
            raise NmapError("O arquivo de alvos não existe ou não é um arquivo.")
        if ports and ports.strip() and top_ports is not None:
            raise NmapError("Portas customizadas e top ports são opções exclusivas.")
        if top_ports is not None and not 1 <= int(top_ports) <= 65535:
            raise NmapError("Top ports deve estar entre 1 e 65535.")
        if version_intensity is not None and not 0 <= int(version_intensity) <= 9:
            raise NmapError("A intensidade de versão deve estar entre 0 e 9.")

        if not self.nmap_path:
            raise NmapError("Executável do Nmap não encontrado no sistema.")

        cmd = [self.nmap_path]

        # Tipo de scan
        if scan_type:
            cmd.append(scan_type)

        # Timing
        if timing:
            cmd.append(f"-{timing}")

        if ipv6:
            cmd.append("-6")

        # Portas
        if ports and ports.strip():
            cmd.extend(["-p", ports.strip()])
        elif top_ports is not None:
            cmd.extend(["--top-ports", str(int(top_ports))])

        if version_intensity is not None:
            cmd.extend(["--version-intensity", str(int(version_intensity))])

        if exclude_targets and exclude_targets.strip():
            cmd.extend(["--exclude", exclude_targets.strip()])

        # Formato de saída
        if output_format == "xml":
            cmd.extend(["-oX", "-"])
        else:
            cmd.extend(["-oN", "-"])

        # Argumentos adicionais
        if extra_args and extra_args.strip():
            try:
                cmd.extend(shlex.split(extra_args))
            except ValueError as e:
                raise NmapError(f"Argumentos extras inválidos: {e}") from e

        # Alvo sempre no final
        if has_input_file:
            cmd.extend(["-iL", input_file.strip()])
        else:
            cmd.append(target.strip())

        return cmd

    def create_process(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "-sS",
        extra_args: str = "",
        timing: str = "T3",
        output_format: str = "normal",
        input_file: Optional[str] = None,
        exclude_targets: str = "",
        ipv6: bool = False,
        top_ports: Optional[int] = None,
        version_intensity: Optional[int] = None,
    ) -> subprocess.Popen:
        """Cria e retorna o processo Popen para streaming em tempo real."""
        cmd = self.build_command(
            target=target,
            ports=ports,
            scan_type=scan_type,
            extra_args=extra_args,
            timing=timing,
            output_format=output_format,
            input_file=input_file,
            exclude_targets=exclude_targets,
            ipv6=ipv6,
            top_ports=top_ports,
            version_intensity=version_intensity,
        )
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

    def run_scan(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "-sS",
        extra_args: str = "",
        timing: str = "T3",
        output_format: str = "normal",
        timeout: Optional[int] = None,
        input_file: Optional[str] = None,
        exclude_targets: str = "",
        ipv6: bool = False,
        top_ports: Optional[int] = None,
        version_intensity: Optional[int] = None,
    ) -> Tuple[str, str, int]:
        """Executa o scan de forma síncrona e retorna (stdout, stderr, returncode)."""
        cmd = self.build_command(
            target=target,
            ports=ports,
            scan_type=scan_type,
            extra_args=extra_args,
            timing=timing,
            output_format=output_format,
            input_file=input_file,
            exclude_targets=exclude_targets,
            ipv6=ipv6,
            top_ports=top_ports,
            version_intensity=version_intensity,
        )
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired:
            raise NmapError("O scan excedeu o tempo limite definido.")
        except FileNotFoundError:
            raise NmapError("Executável do Nmap não encontrado.")
        except Exception as e:
            raise NmapError(f"Erro ao executar o Nmap: {e}")

    @staticmethod
    def get_common_scan_types() -> Dict[str, str]:
        """Retorna os tipos de scan mais comuns com descrição amigável."""
        return {
            "-sS": "SYN Stealth Scan (rápido, padrão)",
            "-sT": "TCP Connect Scan (sem privilégios)",
            "-sV": "Version Detection (versão dos serviços)",
            "-sU": "UDP Scan (portas UDP)",
            "-A":  "Aggressive (OS + Versão + Scripts + Traceroute)",
            "-sn": "Ping Scan (apenas descoberta de hosts)",
            "-sC": "Default Scripts (scripts NSE padrão)",
            "-O":  "OS Detection (detecção do sistema operacional)",
        }
