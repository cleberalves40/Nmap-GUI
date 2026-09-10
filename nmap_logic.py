"""
Módulo de lógica de comandos do Nmap.
Responsável por construir e executar comandos nmap de forma segura.
"""

import shutil
import subprocess
from typing import List, Optional, Tuple


class NmapError(Exception):
    """Exceção personalizada para erros relacionados ao Nmap."""
    pass


class NmapLogic:
    """Classe que encapsula a lógica de execução do Nmap."""

    def __init__(self):
        self.nmap_path = self._find_nmap()
        if not self.nmap_path:
            raise NmapError(
                "Nmap não encontrado no PATH do sistema.\n"
                "Instale o Nmap e certifique-se de que ele está acessível."
            )

    def _find_nmap(self) -> Optional[str]:
        """Procura o executável do nmap no PATH."""
        return shutil.which("nmap")

    def get_version(self) -> str:
        """Retorna a versão do Nmap instalado."""
        try:
            result = subprocess.run(
                [self.nmap_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            # A primeira linha geralmente contém a versão
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
            target: Alvo (IP, hostname ou faixa de rede)
            ports: Portas (ex: "22,80,443" ou "1-1000")
            scan_type: Tipo de scan (ex: -sS, -sT, -sV, -sU, -A)
            extra_args: Argumentos extras livres
            timing: Template de timing (T0 a T5)
            output_format: "normal" ou "xml"

        Returns:
            Lista de argumentos pronta para subprocess
        """
        if not target or not target.strip():
            raise NmapError("O alvo não pode estar vazio.")

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
            cmd.append("-oX")
            cmd.append("-")          # saída XML para stdout
        else:
            cmd.append("-oN")
            cmd.append("-")          # saída normal para stdout

        # Argumentos extras
        if extra_args.strip():
            # Separação simples por espaço (cuidado com aspas em uso real)
            cmd.extend(extra_args.strip().split())

        # Alvo sempre por último
        cmd.append(target.strip())

        return cmd

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
        """
        Executa o scan e retorna (stdout, stderr, returncode).

        Raises:
            NmapError: em caso de erro de construção ou execução
        """
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
                check=False   # não levanta automaticamente
            )
            return process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired:
            raise NmapError("O scan excedeu o tempo limite definido.")
        except FileNotFoundError:
            raise NmapError("Executável do Nmap não encontrado.")
        except Exception as e:
            raise NmapError(f"Erro ao executar o Nmap: {e}")

    def get_common_scan_types(self) -> dict:
        """Retorna os tipos de scan mais comuns com descrição."""
        return {
            "-sS": "SYN Stealth Scan (padrão, requer root/admin)",
            "-sT": "TCP Connect Scan (não requer privilégios)",
            "-sV": "Version Detection",
            "-sU": "UDP Scan",
            "-A":  "Aggressive (OS + Version + Scripts + Traceroute)",
            "-sn": "Ping Scan (descoberta de hosts)",
            "-sC": "Script Scan padrão (NSE)",
            "-O":  "OS Detection",
        }