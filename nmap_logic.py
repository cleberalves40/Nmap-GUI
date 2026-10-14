"""
Módulo de compatibilidade com versão legada.
Redireciona para o pacote nmap_gui.logic.
"""

from nmap_gui.logic import NmapLogic, NmapError

__all__ = ["NmapLogic", "NmapError"]