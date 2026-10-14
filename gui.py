"""
Compatibilidade com versão legada.
Redireciona para o pacote modularizado nmap_gui.
"""

from nmap_gui.window import main, NmapGUI, ScanWorker
from nmap_gui.logic import NmapLogic, NmapError

if __name__ == "__main__":
    main()