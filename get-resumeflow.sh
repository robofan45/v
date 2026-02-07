#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
#  ResumeFlow — Direct Install Script
#
#  Run with:
#    curl -fsSL https://raw.githubusercontent.com/robofan45/v/main/get-resumeflow.sh | bash
#
#  Or with wget:
#    wget -qO- https://raw.githubusercontent.com/robofan45/v/main/get-resumeflow.sh | bash
#
#  What it does:
#    1. Checks that Python 3.11+ is installed
#    2. Checks that git is installed
#    3. Clones the repo to ~/ResumeFlow
#    4. Creates a virtual environment
#    5. Installs all dependencies
#    6. Creates a launch shortcut script
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="https://github.com/robofan45/v.git"
INSTALL_DIR="$HOME/ResumeFlow"
VENV_DIR="$INSTALL_DIR/.venv"

# ── Colors ──
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

echo ""
echo -e "${BOLD}${CYAN}"
echo "  ╔═══════════════════════════════════════════════╗"
echo "  ║                                               ║"
echo "  ║          ResumeFlow — Direct Install           ║"
echo "  ║    Context Switch Tracker for Desktop          ║"
echo "  ║                                               ║"
echo "  ╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Check git ──────────────────────────────────────────────────────
info "Checking for git..."
if ! command -v git &>/dev/null; then
    fail "git is required but not found. Install it from https://git-scm.com"
fi
ok "git found"

# ── 2. Check Python ──────────────────────────────────────────────────
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
    fail "Python 3.11+ is required (found $PY_VERSION). Upgrade at https://python.org"
fi
ok "Python $PY_VERSION"

# ── 3. Clone repo ───────────────────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    info "Directory $INSTALL_DIR already exists — pulling latest..."
    git -C "$INSTALL_DIR" pull --quiet 2>/dev/null || true
    ok "Updated existing installation"
else
    info "Cloning ResumeFlow to $INSTALL_DIR..."
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    ok "Cloned to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── 4. Create virtual environment ───────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    $PY -m venv "$VENV_DIR"
    ok "Virtual environment created"
else
    ok "Virtual environment already exists"
fi

# ── 5. Install dependencies ─────────────────────────────────────────
info "Installing dependencies (this may take a minute)..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet 2>/dev/null
"$VENV_DIR/bin/pip" install -e . --quiet 2>/dev/null
ok "All dependencies installed"

# ── 6. Linux: check xdotool ─────────────────────────────────────────
if [[ "$OSTYPE" == "linux"* ]]; then
    if ! command -v xdotool &>/dev/null; then
        warn "xdotool is needed on Linux for window detection"
        echo -e "       Install with: ${BOLD}sudo apt install xdotool${NC}"
    else
        ok "xdotool found"
    fi
fi

# ── 7. Create launcher shortcut ─────────────────────────────────────
LAUNCHER="$HOME/.local/bin/resumeflow"
mkdir -p "$HOME/.local/bin"
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/usr/bin/env bash
exec "$HOME/ResumeFlow/.venv/bin/resumeflow" "$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"
ok "Launcher created at $LAUNCHER"

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "  ╔═══════════════════════════════════════════════╗"
echo "  ║                                               ║"
echo "  ║         Installation complete!                 ║"
echo "  ║                                               ║"
echo "  ╚═══════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${BOLD}To run ResumeFlow:${NC}"
echo ""
echo -e "    ${GREEN}resumeflow${NC}"
echo ""
echo -e "  If 'resumeflow' is not found, either:"
echo -e "    - Restart your terminal, or"
echo -e "    - Run: ${BOLD}$INSTALL_DIR/.venv/bin/resumeflow${NC}"
echo ""
echo -e "  ${BOLD}Installed to:${NC} $INSTALL_DIR"
echo -e "  ${BOLD}Data stored at:${NC} ~/.resumeflow/"
echo ""
