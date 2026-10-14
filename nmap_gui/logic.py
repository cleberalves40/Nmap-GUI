"""
Módulo de lógica de comandos do Nmap.
Responsável por construir e executar comandos nmap de forma segura.
"""

import shutil
import subprocess
from typing import List, Optional, Tuple, Dict


class NmapError(Exception):
    """Exceção personalizada para erros relacionados ao Nmap."""
    pass


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
        output_format: str = "normal"
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
        if not target or not target.strip():
            raise NmapError("O alvo não pode estar vazio.")

        if not self.nmap_path:
            raise NmapError("Executável do Nmap não encontrado no sistema.")

        cmd = [self.nmap_path]

        # Tipo de scan
        if scan_type:
            cmd.append(scan_type)

        # Timing
        if timing:
            cmd.append(f"-{timing}")

        # Portas
        if ports and ports.strip():
            cmd.extend(["-p", ports.strip()])

        # Formato de saída
        if output_format == "xml":
            cmd.extend(["-oX", "-"])
        else:
            cmd.extend(["-oN", "-"])

        # Argumentos adicionais
        if extra_args and extra_args.strip():
            cmd.extend(extra_args.strip().split())

        # Alvo sempre no final
        cmd.append(target.strip())

        return cmd

    def create_process(
        self,
        target: str,
        ports: str = "",
        scan_type: str = "-sS",
        extra_args: str = "",
        timing: str = "T3",
        output_format: str = "normal"
    ) -> subprocess.Popen:
        """Cria e retorna o processo Popen para streaming em tempo real."""
        cmd = self.build_command(
            target=target,
            ports=ports,
            scan_type=scan_type,
            extra_args=extra_args,
            timing=timing,
            output_format=output_format
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
        timeout: Optional[int] = None
    ) -> Tuple[str, str, int]:
        """Executa o scan de forma síncrona e retorna (stdout, stderr, returncode)."""
        cmd = self.build_command(
            target=target,
            ports=ports,
            scan_type=scan_type,
            extra_args=extra_args,
            timing=timing,
            output_format=output_format
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
