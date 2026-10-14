# Nmap GUI

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Scanner](https://img.shields.io/badge/Security-Nmap-orange.svg)](https://nmap.org/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-yellow.svg)](LICENSE)
[![CI Check](https://github.com/cleberalves40/Nmap-GUI/actions/workflows/lint_test.yml/badge.svg)](https://github.com/cleberalves40/Nmap-GUI/actions/workflows/lint_test.yml)

Uma interface gráfica moderna, rápida e intuitiva em **PyQt6** para o scanner de segurança e rede [Nmap](https://nmap.org/).

Projetada com suporte nativo a múltiplos temas (Dark/Light), streaming de saída em tempo real e exportação de resultados.

---

## ✨ Funcionalidades

- **Streaming em Tempo Real**: Saída do Nmap exibida linha a linha à medida que os resultados são obtidos, sem congelar a interface.
- **Seletor de Temas Dinâmico**:
  - 🎨 **Padrão**: Interface clara, limpa e moderna.
  - 🌑 **Charcoal**: Estilo escuro inspirado na interface do GNS3.
  - 🌌 **Selenized**: Paleta balanceada de contraste suave.
  - ☕ **Catppuccin Frappé**: Tema pastel dark moderno e relaxante aos olhos.
  - *Preferência de tema salva automaticamente para os próximos usos.*
- **Perfis de Varredura Rápidos**:
  - `SYN Stealth Scan (-sS)`
  - `TCP Connect Scan (-sT)`
  - `Version Detection (-sV)`
  - `UDP Scan (-sU)`
  - `Aggressive Scan (-A)`
  - `Ping Scan (-sn)`
  - `Default Script Scan (-sC)`
  - `OS Detection (-O)`
- **Controle Preciso**:
  - Seleção de portas (`-p`) customizadas.
  - Controle de perfis de temporização (`T0` a `T5`).
  - Campo aberto para argumentos extras avançados do Nmap.
  - Opção de saída em XML (`-oX`) para integração com outros sistemas.
  - Timeout configurável por scan.
- **Interrupção Segura**: Botão "Interromper" encerra o processo do Nmap imediatamente, sem processos zumbis em segundo plano.
- **Exportação de Relatórios**: Salve facilmente os resultados da análise em arquivos de texto (`.txt`) ou `.xml`.

---

## 🏛️ Estrutura do Projeto

```text
Nmap-GUI/
├── nmap_gui/                # Pacote Python principal
│   ├── __init__.py
│   ├── __main__.py          # Suporte a: python -m nmap_gui
│   ├── logic.py             # Encapsulamento seguro do Nmap via subprocess
│   ├── themes.py            # Definição das folhas de estilo QSS dos temas
│   └── window.py            # Interface gráfica e streaming com ScanWorker
├── pyproject.toml           # Configuração de empacotamento padrão PEP 517/621
├── requirements.txt         # Dependências do projeto
├── run.py                   # Script de execução rápida
├── nmap-gui.desktop         # Entrada para menu de aplicativos desktop
├── .github/workflows/       # CI/CD automatizado
│   └── lint_test.yml
├── LICENSE                  # Licença BSD-3-Clause
└── README.md
```

---

## 📦 Pré-requisitos

1. **Python 3.8+** instalado.
2. **Nmap** instalado e acessível no `PATH` do sistema:
   - **FreeBSD**: `pkg install nmap`
   - **Ubuntu / Debian**: `sudo apt install nmap`
   - **Arch Linux**: `sudo pacman -S nmap`
   - **macOS**: `brew install nmap`

---

## 🚀 Instalação e Execução

### Opção 1: Execução Direta (Recomendado para uso rápido)

```bash
# 1. Clonar o repositório
git clone https://github.com/cleberalves40/Nmap-GUI.git
cd Nmap-GUI

# 2. Criar e ativar um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate   # No Windows: .venv\Scripts\activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Iniciar o aplicativo
python3 run.py
```

### Opção 2: Instalação como Pacote do Sistema / Usuário

```bash
pip install .
nmap-gui
```

Ou execute como módulo:

```bash
python3 -m nmap_gui
```

---

## 💡 Dica de Privilégios (SYN Scan & OS Detection)

Alguns tipos de varredura (como `-sS` e `-O`) exigem privilégios de superusuário (`root`):

- **No Linux/FreeBSD**: Você pode executar com `sudo` ou definir as permissões necessárias no binário com `setcap`:
  ```bash
  sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which nmap)
  ```
- Alternativamente, selecione o modo **TCP Connect Scan (`-sT`)**, que roda perfeitamente sem permissões especiais.

---

## 📄 Licença

Distribuído sob a licença [BSD 3-Clause](LICENSE).
