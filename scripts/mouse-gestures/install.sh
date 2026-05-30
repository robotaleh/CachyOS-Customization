#!/usr/bin/env bash
# install.sh – Instala el daemon de gestos de ratón para KDE Plasma en CachyOS
# Uso: bash install.sh
#
# Este script:
#   1. Verifica e instala dependencias (python-evdev, qt6-tools)
#   2. Añade el usuario al grupo 'input' si no está
#   3. Instala el daemon en /usr/local/bin/
#   4. Instala y activa el servicio systemd de usuario

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_SRC="${SCRIPT_DIR}/mouse-gesture-shortcuts.py"
BIN_DEST="/usr/local/bin/mouse-gesture-shortcuts"
SERVICE_SRC="${SCRIPT_DIR}/mouse-gesture-shortcuts.service"
SERVICE_NAME="mouse-gesture-shortcuts.service"
USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"
DROPIN_DIR="${USER_SYSTEMD_DIR}/mouse-gesture-shortcuts.service.d"

# ── Colores ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
_info()  { echo -e "${GREEN}[+]${NC} $*"; }
_warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
_err()   { echo -e "${RED}[✗]${NC} $*" >&2; }
_step()  { echo -e "\n${CYAN}${BOLD}── $* ──────────────────────────────${NC}"; }
_ok()    { echo -e "${GREEN}${BOLD}[✓]${NC} $*"; }

# ── 0. Detener el servicio antes de tocar nada ────────────────────────────────
# Crítico: el daemon captura el ratón de forma exclusiva (grab). Si está
# corriendo durante la instalación, --detect-once no puede leer eventos
# y sobrescribir el binario en caliente puede causar comportamiento inesperado.
if systemctl --user is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
    _info "Deteniendo servicio en ejecución..."
    systemctl --user stop "${SERVICE_NAME}"
    _ok "Servicio detenido"
fi

# ── 1. Verificar dependencias ──────────────────────────────────────────────────
_step "Dependencias"

PKGS_TO_INSTALL=()

if ! python3 -c "import evdev" &>/dev/null; then
    PKGS_TO_INSTALL+=(python-evdev)
else
    _info "python-evdev: ya instalado"
fi

# qt6-tools proporciona qdbus en CachyOS/Arch
QDBUS_FOUND=false
for cmd in qdbus qdbus6 qdbus-qt6 qdbus-qt5; do
    if command -v "$cmd" &>/dev/null; then
        QDBUS_FOUND=true
        _info "qdbus: $(command -v "$cmd")"
        break
    fi
done

if ! $QDBUS_FOUND; then
    PKGS_TO_INSTALL+=(qt6-tools)
fi

if [[ ${#PKGS_TO_INSTALL[@]} -gt 0 ]]; then
    _info "Instalando: ${PKGS_TO_INSTALL[*]}"
    sudo pacman -S --needed --noconfirm "${PKGS_TO_INSTALL[@]}"
fi

# Verificar spectacle
if ! command -v spectacle &>/dev/null; then
    _warn "spectacle no encontrado. El gesto de captura de pantalla no funcionará."
    _warn "  sudo pacman -S spectacle"
fi

# ── 2. Grupo 'input' ───────────────────────────────────────────────────────────
_step "Grupo 'input'"

if ! groups "${USER}" | grep -qw input; then
    _info "Añadiendo ${USER} al grupo 'input'..."
    sudo usermod -aG input "${USER}"
    echo ""
    _warn "╔════════════════════════════════════════════════════════════════╗"
    _warn "║  ACCIÓN REQUERIDA: Cierra sesión y vuelve a entrar.           ║"
    _warn "║  El cambio de grupo solo tiene efecto en nuevas sesiones.     ║"
    _warn "║  Después, ejecuta este script de nuevo para continuar.        ║"
    _warn "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 1
fi

_ok "Usuario ${USER} pertenece al grupo 'input'"

# ── 2b. Regla udev para /dev/uinput ───────────────────────────────────────────
# El daemon crea un dispositivo UInput virtual para reenviar los clics de ratón.
# Sin esta regla, /dev/uinput puede ser de solo root y la pasarela no funciona.
UDEV_RULE_FILE="/etc/udev/rules.d/60-mouse-gesture-uinput.rules"
UDEV_RULE_CONTENT='KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"'

if [[ ! -f "${UDEV_RULE_FILE}" ]] || ! grep -qF 'mouse-gesture' "${UDEV_RULE_FILE}" 2>/dev/null; then
    _info "Instalando regla udev para /dev/uinput..."
    echo "# mouse-gesture-shortcuts: acceso al grupo 'input'" | sudo tee "${UDEV_RULE_FILE}" > /dev/null
    echo "${UDEV_RULE_CONTENT}"                               | sudo tee -a "${UDEV_RULE_FILE}" > /dev/null
    sudo udevadm control --reload-rules
    sudo udevadm trigger --name-match=uinput
    _ok "Regla udev instalada: ${UDEV_RULE_FILE}"
else
    _info "Regla udev para uinput: ya existe"
fi

# ── 3. Instalar el daemon ──────────────────────────────────────────────────────
_step "Instalando daemon"

_info "${BIN_SRC} → ${BIN_DEST}"
sudo install -m 755 "${BIN_SRC}" "${BIN_DEST}"
_ok "Daemon instalado en ${BIN_DEST}"

# ── 4. Instalar el servicio systemd de usuario ─────────────────────────────────
_step "Servicio systemd de usuario"

mkdir -p "${USER_SYSTEMD_DIR}"
install -m 644 "${SERVICE_SRC}" "${USER_SYSTEMD_DIR}/${SERVICE_NAME}"
systemctl --user daemon-reload
_ok "Servicio instalado en ${USER_SYSTEMD_DIR}/${SERVICE_NAME}"

# ── 5. Detección interactiva del dispositivo ──────────────────────────────────
_step "Detección del ratón"

DETECTED_DEVICE=""

# Si ya existe device.conf de una instalación anterior, preguntar si reconfigurar
if [[ -f "${DROPIN_DIR}/device.conf" ]]; then
    EXISTING_DEV=$(grep -oP '(?<=MOUSE_DEVICE=)/dev/input/event\d+' "${DROPIN_DIR}/device.conf" || true)
    EXISTING_NAME=$(cat "/sys/class/input/$(basename "${EXISTING_DEV:-x}")/device/name" 2>/dev/null || echo "desconocido")
    _info "Configuración existente: ${EXISTING_DEV:-ninguna}  (${EXISTING_NAME})"
    echo -e -n "  ${CYAN}¿Reconfigurar el ratón? [s/N]:${NC} "
    read -r RECONFIG </dev/tty
    if [[ ! "${RECONFIG}" =~ ^[sS]$ ]]; then
        _ok "Manteniendo configuración existente."
        SKIP_DETECTION=true
    else
        SKIP_DETECTION=false
    fi
else
    SKIP_DETECTION=false
fi

if [[ "${SKIP_DETECTION}" == false ]]; then
    # Contar cuántos candidatos físicos hay
    CANDIDATE_COUNT=$("${BIN_DEST}" --list-devices 2>/dev/null | grep -c '/dev/input/' || true)

    if [[ "${CANDIDATE_COUNT}" -eq 0 ]]; then
        _warn "No se encontró ningún ratón con botones laterales."
        _warn "El daemon intentará detectarlo al arrancar."
        _warn "Si falla, define MOUSE_DEVICE en: ${DROPIN_DIR}/device.conf"

    elif [[ "${CANDIDATE_COUNT}" -eq 1 ]]; then
        # Solo un candidato → usarlo directamente sin preguntar
        DETECTED_DEVICE=$("${BIN_DEST}" --list-devices 2>/dev/null | grep -oP '/dev/input/event\d+' | head -1)
        DEVICE_NAME=$(cat "/sys/class/input/$(basename "${DETECTED_DEVICE}")/device/name" 2>/dev/null || echo "desconocido")
        _ok "Único candidato: ${DETECTED_DEVICE}  (${DEVICE_NAME})"

    else
        # Varios candidatos → detección interactiva
        echo ""
        _info "Se detectaron ${CANDIDATE_COUNT} ratones con botones laterales."
        echo -e "  ${CYAN}Pulsa${NC} el botón ${BOLD}ADELANTE${NC} o ${BOLD}ATRÁS${NC} en tu ratón para identificarlo..."
        echo ""

        # --detect-once escribe instrucciones a stderr (visibles al usuario en /dev/tty)
        # y solo la ruta del dispositivo a stdout (capturada aquí)
        DETECTED_DEVICE=$("${BIN_DEST}" --detect-once --detect-timeout 30 2>/dev/tty) || true

        if [[ -z "${DETECTED_DEVICE}" ]]; then
            _warn "No se identificó el ratón (tiempo agotado o saltado)."
            _warn "El daemon elegirá el primero disponible al arrancar."
            _warn "Puedes configurarlo después con:"
            _warn "  ${BIN_DEST} --detect-once  y editar ${DROPIN_DIR}/device.conf"
        fi
    fi

    if [[ -n "${DETECTED_DEVICE}" ]]; then
        DEVICE_NAME=$(cat "/sys/class/input/$(basename "${DETECTED_DEVICE}")/device/name" 2>/dev/null || echo "desconocido")
        _ok "Ratón seleccionado: ${DETECTED_DEVICE}  (${DEVICE_NAME})"

        mkdir -p "${DROPIN_DIR}"
        cat > "${DROPIN_DIR}/device.conf" <<EOF
# Generado por install.sh – modifica si tienes varios ratones
[Service]
Environment=MOUSE_DEVICE=${DETECTED_DEVICE}
EOF
        systemctl --user daemon-reload
        _info "Configuración guardada en ${DROPIN_DIR}/device.conf"
    fi
fi

# ── 6. Activar y arrancar el servicio ─────────────────────────────────────────
_step "Activando servicio"

systemctl --user enable --now "${SERVICE_NAME}"
sleep 1

if systemctl --user is-active --quiet "${SERVICE_NAME}"; then
    _ok "Servicio activo y en ejecución"
else
    _warn "El servicio no arrancó correctamente."
    _warn "Consulta los logs: journalctl --user -u ${SERVICE_NAME} -n 20"
fi

# ── 7. Resumen ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║           Instalación completada con éxito ✓                ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Gestos activos:"
echo "    ADELANTE (mantener ${MGS_HOLD_TIME:-0.4}s)       → Captura de pantalla (región)"
echo "    ATRÁS + mover ARRIBA         → Mosaico ventanas (escritorio actual)"
echo "    ATRÁS + mover DERECHA        → Escritorio virtual siguiente"
echo "    ATRÁS + mover IZQUIERDA      → Escritorio virtual anterior"
echo ""
echo "  Comandos útiles:"
echo "    systemctl --user status  ${SERVICE_NAME}"
echo "    systemctl --user restart ${SERVICE_NAME}"
echo "    journalctl --user -u ${SERVICE_NAME} -f"
echo ""
echo "  Ajustar sensibilidad (edita el drop-in de configuración):"
echo "    ${DROPIN_DIR}/device.conf"
echo "    MGS_HOLD_TIME=0.4         # segundos para activar captura"
echo "    MGS_MOVE_THRESHOLD=80     # píxeles para activar gesto ATRÁS"
echo ""
echo "  Desinstalar:"
echo "    bash ${SCRIPT_DIR}/uninstall.sh"
echo ""
