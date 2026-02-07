#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
#  ResumeFlow — one-command installer for macOS and Linux
# ──────────────────────────────────────────────────────────
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        ResumeFlow Installer          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# --- Check Python -------------------------------------------------------
info "Checking Python version..."
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    fail "Python 3.11+ is required but not found. Install it from https://python.org"
fi

PY_VERSION=$($PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PY -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PY -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    fail "Python 3.11+ is required (found $PY_VERSION). Please upgrade."
fi
ok "Python $PY_VERSION found"

# --- Create virtual environment -----------------------------------------
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    $PY -m venv "$VENV_DIR"
    ok "Virtual environment created at $VENV_DIR/"
else
    ok "Virtual environment already exists"
fi

# --- Activate and install -----------------------------------------------
info "Installing ResumeFlow and dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -e . --quiet
ok "Dependencies installed"

# --- Linux: check for xdotool ------------------------------------------
if [[ "$OSTYPE" == "linux"* ]]; then
    if ! command -v xdotool &>/dev/null; then
        warn "xdotool is required on Linux for window detection."
        echo "       Install it with:  sudo apt install xdotool  (Debian/Ubuntu)"
        echo "                         sudo dnf install xdotool  (Fedora)"
        echo "                         sudo pacman -S xdotool    (Arch)"
    else
        ok "xdotool found"
    fi
fi

# --- Done ---------------------------------------------------------------
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Installation complete!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  To run ResumeFlow:"
echo ""
echo "    source $VENV_DIR/bin/activate"
echo "    resumeflow"
echo ""
echo "  Or simply:"
echo ""
echo "    $VENV_DIR/bin/resumeflow"
echo ""
