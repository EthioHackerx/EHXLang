#!/usr/bin/env bash
# =====================================================================
#   EHXLang v1.0.0 Linux / macOS Universal Installer
#   Developed by Yonatan Muluken ( ETHIO HACKER X )
# =====================================================================

set -e

APP_NAME="EHXLang"
VERSION="1.0.0"
INSTALL_DIR="$HOME/.local/share/ehxlang"
BIN_DIR="$HOME/.local/bin"

echo "====================================================================="
echo "  EHXLang v1.0.0 - Universal Installer (Linux / macOS)"
echo "  Developed by Yonatan Muluken ( ETHIO HACKER X )"
echo "====================================================================="
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "[-] Error: python3 is required but was not found on your system."
    echo "    Please install Python 3.10+ (e.g., sudo apt install python3)"
    exit 1
fi

echo "[*] Target installation directory: $INSTALL_DIR"
echo "[*] Target binary symlink:         $BIN_DIR/ehx"

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Copying runtime files..."
cp "$SCRIPT_DIR/ehx.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/lexer.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/parser.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/tokens.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/interpreter.py" "$INSTALL_DIR/"

# Create executable launcher script
LAUNCHER="$BIN_DIR/ehx"
cat << 'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
INSTALL_DIR="$HOME/.local/share/ehxlang"
exec python3 "$INSTALL_DIR/ehx.py" "$@"
EOF

chmod +x "$LAUNCHER"

# Install VS Code extension if VS Code directory exists
VSCODE_EXT_DIR="$HOME/.vscode/extensions/ehx-vscode"
if [ -d "$HOME/.vscode" ] && [ -d "$SCRIPT_DIR/ehx-vscode" ]; then
    echo "[*] Installing VS Code extension..."
    mkdir -p "$VSCODE_EXT_DIR"
    cp -r "$SCRIPT_DIR/ehx-vscode/"* "$VSCODE_EXT_DIR/"
fi

# Ensure ~/.local/bin is in PATH
SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            echo "[*] Added $BIN_DIR to your PATH in $SHELL_RC"
        fi
    fi
fi

echo ""
echo "====================================================================="
echo "  [SUCCESS] $APP_NAME $VERSION installed successfully!"
echo "====================================================================="
echo "  You can now run:"
echo "    ehx <file.ehx>        # Run an EHXLang script"
echo "    ehx run <file.ehx>    # Run an EHXLang script"
echo "    ehx repl              # Start the interactive shell"
echo "    ehx -v                # Check version and official channels"
echo ""
echo "  (Note: Run 'source $SHELL_RC' or restart your terminal if 'ehx' is not recognized yet)"
echo "====================================================================="
