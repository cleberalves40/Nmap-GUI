"""
Compatibilidade com versão legada multi-tema.
Redireciona para o pacote modularizado nmap_gui.
"""

from nmap_gui.window import main, NmapGUI, ScanWorker
from nmap_gui.logic import NmapLogic, NmapError
from nmap_gui.themes import THEMES

if __name__ == "__main__":
    main()