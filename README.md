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
- **Perfis Salvos**: Armazene configurações de scan com nome, aplique-as novamente e remova perfis existentes.
- **Controle Preciso**:
  - Seleção de portas (`-p`) customizadas.
  - Importação de listas de alvos (`-iL`) e exclusão de hosts/redes (`--exclude`).
  - Seleção explícita de IPv6 (`-6`).
  - Varredura das N portas mais comuns (`--top-ports`), exclusiva com portas customizadas.
  - Intensidade de detecção de versão (`--version-intensity`, 0 a 9), disponível com `-sV` ou `-A`.
  - Controle de perfis de temporização (`T0` a `T5`).
  - Campo aberto para argumentos extras avançados do Nmap.
  - Opção de saída em XML (`-oX`) para integração com outros sistemas.
  - Timeout configurável por scan.
- **Interrupção Segura**: Botão "Interromper" encerra o processo do Nmap imediatamente, sem processos zumbis em segundo plano.
- **Resultados Estruturados**: Consulte hosts, portas, estados, serviços, versões e scripts em uma tabela filtrável a partir da saída XML.
- **Histórico Local**: Execuções concluídas são mantidas entre sessões no diretório de dados da aplicação definido pelo Qt.
- **Comparação de Scans**: Compare dois resultados XML e veja hosts e portas adicionados, removidos ou alterados.
- **Exportação de Relatórios**: Salve a saída original do Nmap em `.txt` ou o XML validado sem texto da interface.
- **Verificação de Versão**: Consulte manualmente a versão estável upstream; o app apenas informa se há atualização e não instala software.

O histórico contém um `history.json`, os perfis em `profiles.json` e os artefatos das execuções em `results/`, dentro de `QStandardPaths.AppDataLocation`. A comparação requer que ambos os scans tenham sido executados com saída XML.

A verificação de versão é iniciada pelo usuário e consulta somente as tags públicas do repositório upstream do Nmap no GitHub. Ela requer conexão com a internet; nenhum resultado de scan ou alvo é enviado. A instalação de uma versão nova é sempre manual.

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

## Releases

Para publicar uma release, atualize `project.version` em `pyproject.toml`, valide a CI e envie uma tag correspondente, por exemplo `v1.0.1`. O workflow verifica a correspondência e publica os arquivos source e wheel; nenhum release é criado sem o envio explícito da tag.

---

## Compatibilidade e Privilégios

Linux, FreeBSD e macOS são os sistemas documentados neste projeto; a CI executa em Ubuntu. O Windows não está validado pela CI.

Scans com pacotes brutos, como SYN (`-sS`) e detecção de sistema operacional (`-O`), normalmente precisam de privilégios elevados:

- **Linux**: execute com `sudo`. Como alternativa, administradores podem conceder capacidades ao binário `nmap`; isso altera privilégios persistentes e deve ser avaliado antes do uso:
  ```bash
  sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which nmap)
  ```
- **FreeBSD e macOS**: execute com `sudo`/`doas` conforme a configuração do sistema.
- **Sem privilégios elevados**: selecione **TCP Connect Scan (`-sT`)**.

---

## 📄 Licença

Distribuído sob a licença [BSD 3-Clause](LICENSE).
