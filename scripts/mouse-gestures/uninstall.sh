#!/usr/bin/env bash
# uninstall.sh – Elimina el daemon de gestos de ratón
set -euo pipefail

BIN_DEST="/usr/local/bin/mouse-gesture-shortcuts"
SERVICE_NAME="mouse-gesture-shortcuts.service"
USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
_info() { echo -e "${GREEN}[+]${NC} $*"; }
_warn() { echo -e "${YELLOW}[!]${NC} $*"; }

_info "Deteniendo y desactivando servicio..."
systemctl --user stop    "${SERVICE_NAME}" 2>/dev/null || true
systemctl --user disable "${SERVICE_NAME}" 2>/dev/null || true

_info "Eliminando archivos del servicio..."
rm -f  "${USER_SYSTEMD_DIR}/${SERVICE_NAME}"
rm -rf "${USER_SYSTEMD_DIR}/mouse-gesture-shortcuts.service.d"
systemctl --user daemon-reload

if [[ -f "${BIN_DEST}" ]]; then
    _info "Eliminando ${BIN_DEST}..."
    sudo rm -f "${BIN_DEST}"
fi

UDEV_RULE="/etc/udev/rules.d/60-mouse-gesture-uinput.rules"
if [[ -f "${UDEV_RULE}" ]]; then
    _info "Eliminando regla udev ${UDEV_RULE}..."
    sudo rm -f "${UDEV_RULE}"
    sudo udevadm control --reload-rules
fi

_warn "El usuario sigue en el grupo 'input'. Para eliminarlo:"
_warn "  sudo gpasswd -d ${USER} input  (requiere cierre de sesión)"

echo ""
echo -e "${GREEN}Desinstalación completa.${NC}"
