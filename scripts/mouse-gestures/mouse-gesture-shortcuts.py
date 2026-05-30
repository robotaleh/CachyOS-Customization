#!/usr/bin/env python3
"""
mouse-gesture-shortcuts.py  -  KDE Plasma / Wayland
====================================================
Daemon que lee eventos raw del ratón y dispara acciones de KDE
basándose en gestos de botón (hold) y botón + movimiento.

Gestos
------
  ADELANTE  mantenido (≥ HOLD_TIME s)   → Captura de pantalla (Spectacle, región)
  ATRÁS     + mover ARRIBA              → Mosaico de ventanas (escritorio actual)
  ATRÁS     + mover ABAJO               → Preview de todos los escritorios
  ATRÁS     + mover DERECHA             → Escritorio virtual anterior
  ATRÁS     + mover IZQUIERDA           → Escritorio virtual siguiente

  Los clics rápidos de ADELANTE / ATRÁS siguen funcionando con normalidad.

Requisitos
----------
  python-evdev        sudo pacman -S python-evdev
  qt6-tools           sudo pacman -S qt6-tools   (provee qdbus)
  El usuario debe estar en el grupo 'input'

Variables de entorno
--------------------
  MOUSE_DEVICE        /dev/input/eventX  (auto-detectado si no se define)
  MGS_HOLD_TIME       Segundos para mantener ADELANTE antes del trigger  (def: 0.4)
  MGS_MOVE_THRESHOLD  Píxeles de movimiento para activar gestos de ATRÁS (def: 80)
"""

import argparse
import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from typing import Optional

try:
    import evdev
    from evdev import InputDevice, UInput, ecodes, list_devices
except ImportError:
    print("Error: python-evdev no está instalado.")
    print("  sudo pacman -S python-evdev")
    sys.exit(1)

# ─────────────────────────────── Configuración ────────────────────────────────

FORWARD_HOLD_TIME   = float(os.environ.get("MGS_HOLD_TIME",       "0.4"))
MOVEMENT_THRESHOLD  = int(  os.environ.get("MGS_MOVE_THRESHOLD",  "80"))

# ──────────────────────────────── Logging ─────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mouse-gestures")

# ──────────────────────── Acciones KDE vía D-Bus ──────────────────────────────

def _find_qdbus() -> Optional[str]:
    """Localiza el binario qdbus disponible en el sistema."""
    for name in ("qdbus", "qdbus6", "qdbus-qt6", "qdbus-qt5"):
        path = shutil.which(name)
        if path:
            return path
    return None

QDBUS: Optional[str] = _find_qdbus()


def _run_bg(cmd: list[str]) -> None:
    """Lanza un comando en segundo plano (fire-and-forget)."""
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log.error("Comando no encontrado: %s", cmd[0])
    except OSError as exc:
        log.error("Error al lanzar '%s': %s", cmd[0], exc)


def gesture_screenshot() -> None:
    """Abre Spectacle en modo selección de región interactiva."""
    log.info("Gesto → captura de pantalla (región)")
    _run_bg(["spectacle", "--region", "--background"])


def gesture_present_windows() -> None:
    """Muestra las ventanas del escritorio actual (efecto KWin)."""
    log.info("Gesto → mosaico de ventanas (escritorio actual)")
    if not QDBUS:
        log.warning("qdbus no encontrado - instala qt6-tools: sudo pacman -S qt6-tools")
        return
    # "Expose" = Present Windows (Current Desktop) en kglobalaccel de KWin
    _run_bg([QDBUS, "org.kde.kglobalaccel", "/component/kwin",
             "invokeShortcut", "Expose"])


def gesture_present_all_desktops() -> None:
    """Muestra la preview de todos los escritorios virtuales (efecto KWin)."""
    log.info("Gesto → preview de todos los escritorios")
    if not QDBUS:
        log.warning("qdbus no encontrado - instala qt6-tools: sudo pacman -S qt6-tools")
        return
    # "Grid View" = Desktop Grid (cuadrícula de escritorios) en kglobalaccel de KWin
    _run_bg([QDBUS, "org.kde.kglobalaccel", "/component/kwin",
             "invokeShortcut", "Grid View"])


def gesture_next_desktop() -> None:
    """Cambia al escritorio virtual siguiente (sin saltar al primero al llegar al último)."""
    log.info("Gesto → escritorio siguiente")
    if not QDBUS:
        log.warning("qdbus no encontrado - instala qt6-tools")
        return
    # invokeShortcut replica exactamente Ctrl+Super+Derecha: respeta el borde final
    _run_bg([QDBUS, "org.kde.kglobalaccel", "/component/kwin",
             "invokeShortcut", "Switch to Next Desktop"])


def gesture_prev_desktop() -> None:
    """Cambia al escritorio virtual anterior (sin saltar al último al llegar al primero)."""
    log.info("Gesto → escritorio anterior")
    if not QDBUS:
        log.warning("qdbus no encontrado - instala qt6-tools")
        return
    # invokeShortcut replica exactamente Ctrl+Super+Izquierda: respeta el borde inicial
    _run_bg([QDBUS, "org.kde.kglobalaccel", "/component/kwin",
             "invokeShortcut", "Switch to Previous Desktop"])

# ─────────────────────── Búsqueda de dispositivo ──────────────────────────────

# Nombres de dispositivos virtuales que nunca queremos usar como ratón real
_VIRTUAL_NAMES = (
    "mouse-gesture-passthrough",  # nuestro propio UInput
    "ydotoold virtual device",
    "py-evdev-uinput",
)


def _is_virtual(dev: "InputDevice") -> bool:
    """True si el dispositivo es virtual/sintético y debe ignorarse."""
    name_lower = dev.name.lower()
    return any(v.lower() in name_lower for v in _VIRTUAL_NAMES)


def _has_side_buttons(dev: "InputDevice") -> bool:
    caps = dev.capabilities()
    keys = caps.get(ecodes.EV_KEY, [])
    return (ecodes.BTN_EXTRA in keys) or (ecodes.BTN_SIDE in keys)


def find_side_button_mouse() -> Optional[str]:
    """Devuelve la ruta del primer ratón físico que tenga BTN_EXTRA o BTN_SIDE."""
    for path in list_devices():
        try:
            dev = InputDevice(path)
            ok = _has_side_buttons(dev) and not _is_virtual(dev)
            dev.close()
            if ok:
                return path
        except (PermissionError, OSError):
            pass
    return None


def print_side_button_mice() -> None:
    """Muestra en pantalla los ratones físicos con botones laterales disponibles."""
    found = False
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if _has_side_buttons(dev) and not _is_virtual(dev):
                if not found:
                    print("Ratones con botones laterales detectados:")
                    found = True
                print(f"  {path}  →  {dev.name}")
            dev.close()
        except (PermissionError, OSError):
            pass
    if not found:
        print("No se encontró ningún ratón con botones laterales.")
        print("Asegúrate de estar en el grupo 'input': sudo usermod -aG input $USER")


def detect_once(timeout: float = 30.0) -> Optional[str]:
    """
    Espera a que el usuario pulse un botón lateral y devuelve la ruta del
    dispositivo detectado. Mensajes al usuario → stderr. Ruta → stdout.
    Devuelve None si se agota el tiempo o se interrumpe.
    """
    import select as _select

    candidates: list = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if _has_side_buttons(dev) and not _is_virtual(dev):
                candidates.append(dev)
            else:
                dev.close()
        except (PermissionError, OSError):
            pass

    if not candidates:
        print(
            "No se encontró ningún ratón con botones laterales.\n"
            "Asegúrate de estar en el grupo 'input': sudo usermod -aG input $USER",
            file=sys.stderr,
        )
        return None

    SIDE_NAMES = {
        ecodes.BTN_SIDE:    "ATRÁS   (BTN_SIDE)",
        ecodes.BTN_EXTRA:   "ADELANTE (BTN_EXTRA)",
        ecodes.BTN_FORWARD: "ADELANTE (BTN_FORWARD)",
        ecodes.BTN_BACK:    "ATRÁS   (BTN_BACK)",
    }

    print("Candidatos detectados:", file=sys.stderr)
    for dev in candidates:
        print(f"  {dev.path}  {dev.name}", file=sys.stderr)
    print(
        f"\nPulsa ADELANTE o ATRÁS en tu ratón... "
        f"({timeout:.0f}s de tiempo límite, Ctrl-C para saltar)\n",
        file=sys.stderr,
    )

    SIDE_CODES = {
        ecodes.BTN_SIDE, ecodes.BTN_EXTRA,
        ecodes.BTN_FORWARD, ecodes.BTN_BACK,
    }
    fds = {dev.fd: dev for dev in candidates}
    detected: Optional[str] = None

    try:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print("Tiempo límite agotado.", file=sys.stderr)
                break
            r, _, _ = _select.select(fds.keys(), [], [], min(remaining, 1.0))
            for fd in r:
                dev = fds[fd]
                for event in dev.read():
                    if (
                        event.type == ecodes.EV_KEY
                        and event.value == 1
                        and event.code in SIDE_CODES
                    ):
                        btn_name = SIDE_NAMES.get(event.code, f"code={event.code}")
                        print(
                            f"  ★ Detectado: '{dev.name}'  →  {btn_name}",
                            file=sys.stderr,
                        )
                        detected = dev.path
                        return detected
    except KeyboardInterrupt:
        print("\nSaltado.", file=sys.stderr)
    finally:
        for dev in candidates:
            try:
                dev.close()
            except OSError:
                pass

    return detected


def detect_interactive() -> None:
    """
    Modo interactivo: monitoriza todos los ratones detectados y muestra
    cuál responde al pulsar los botones laterales.
    Pulsa Ctrl-C para salir.
    """
    import select

    candidates = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if _has_side_buttons(dev) and not _is_virtual(dev):
                candidates.append(dev)
            else:
                dev.close()
        except (PermissionError, OSError):
            pass

    if not candidates:
        print("No se encontró ningún ratón con botones laterales.")
        print("Asegúrate de estar en el grupo 'input': sudo usermod -aG input $USER")
        return

    SIDE_NAMES = {
        ecodes.BTN_SIDE:    "ATRÁS (BTN_SIDE)",
        ecodes.BTN_EXTRA:   "ADELANTE (BTN_EXTRA)",
        ecodes.BTN_FORWARD: "ADELANTE (BTN_FORWARD)",
        ecodes.BTN_BACK:    "ATRÁS (BTN_BACK)",
    }

    print("\nMonitorizando los siguientes dispositivos:")
    for dev in candidates:
        print(f"  {dev.path}  {dev.name}")
    print("\nPulsa el botón ADELANTE o ATRÁS de tu ratón para identificarlo.")
    print("Ctrl-C para salir.\n")

    fds = {dev.fd: dev for dev in candidates}
    try:
        while True:
            r, _, _ = select.select(fds.keys(), [], [], 1.0)
            for fd in r:
                dev = fds[fd]
                for event in dev.read():
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        btn_name = SIDE_NAMES.get(event.code)
                        if btn_name:
                            print(
                                f"  ★ DETECTADO  {dev.path}  '{dev.name}'  →  {btn_name}\n"
                                f"    Usa: --device {dev.path}"
                            )
    except KeyboardInterrupt:
        print("\nSaliendo.")
    finally:
        for dev in candidates:
            try:
                dev.close()
            except OSError:
                pass

# ──────────────────────────────── Servicio ────────────────────────────────────

class MouseGestureService:
    """
    Captura eventos del ratón en exclusiva y aplica la lógica de gestos.
    Los eventos no consumidos se reenvían a través de un dispositivo UInput
    virtual para que el ratón siga funcionando con normalidad.
    """

    def __init__(self, device_path: str):
        self._device = InputDevice(device_path)
        log.info("Dispositivo físico: %s (%s)", self._device.name, device_path)

        # Crear el dispositivo virtual ANTES de hacer grab() al original.
        # El sleep da tiempo a que libinput/KWin descubra el nuevo dispositivo
        # a través de udev antes de que el original quede capturado. Sin este
        # retardo, hay una ventana en la que ningún dispositivo está activo
        # para el compositor, lo que puede causar que los eventos de botón
        # desde UInput no se entreguen correctamente a las aplicaciones.
        self._ui = self._create_uinput()
        log.info("UInput pasarela: %s", self._ui.device.path)
        log.info("Esperando a que libinput registre el dispositivo virtual...")
        time.sleep(1.0)
        self._device.grab()
        log.info("Captura exclusiva activada. Los clics rápidos se reenvían normalmente.")

        # ── Estado botón ADELANTE ─────────────────────────────────────────
        self._fwd_pressed    = False
        self._fwd_triggered  = False
        self._fwd_timer: Optional[threading.Timer] = None
        self._fwd_buf: list  = []    # eventos en espera de reenvío

        # ── Estado botón ATRÁS ────────────────────────────────────────────
        self._back_pressed    = False
        self._back_triggered  = False
        self._back_press_ev   = None  # evento de pulsación en espera
        self._dx              = 0
        self._dy              = 0

        self._lock    = threading.RLock()
        self._running = True

    def _create_uinput(self) -> UInput:
        """Crea el dispositivo UInput de reenvío copiando todas las propiedades del dispositivo real."""
        # Copiar input_props (p.ej. INPUT_PROP_POINTER) del dispositivo físico.
        # UInput.from_device() no las copia automáticamente en todas las versiones
        # de python-evdev, y libinput las usa para clasificar correctamente el
        # dispositivo como puntero y entregarle todos los eventos de botón.
        try:
            dev_props = list(self._device.input_props)
        except Exception:
            dev_props = []

        try:
            ui = UInput.from_device(
                self._device,
                name="mouse-gesture-passthrough",
                vendor=self._device.info.vendor,
                product=self._device.info.product,
                input_props=dev_props,
            )
            log.debug("UInput creado desde dispositivo original (input_props=%s)", dev_props)
            return ui
        except Exception as exc:
            log.warning("UInput.from_device falló (%s); fallback a copia de capacidades.", exc)

        # Fallback: copiar las capacidades reales del dispositivo en lugar de
        # usar una lista hardcoded que podría omitir códigos relevantes.
        try:
            caps = dict(self._device.capabilities(absinfo=False))
            caps.pop(ecodes.EV_SYN, None)   # UInput gestiona EV_SYN implícitamente
            ui = UInput(
                caps,
                name="mouse-gesture-passthrough",
                vendor=self._device.info.vendor,
                product=self._device.info.product,
                input_props=dev_props,
            )
            log.debug("UInput creado con capacidades copiadas (input_props=%s)", dev_props)
            return ui
        except Exception as exc2:
            log.error("Fallo crítico al crear UInput: %s", exc2)
            raise

    # ── Helpers de escritura ──────────────────────────────────────────────────

    def _emit(self, event) -> None:
        """Reenvía un evento al dispositivo virtual."""
        try:
            self._ui.write(event.type, event.code, event.value)
        except OSError:
            pass

    def _sync(self) -> None:
        try:
            self._ui.syn()
        except OSError:
            pass

    def _replay_fwd(self) -> None:
        """Reenvía los eventos de ADELANTE almacenados en buffer."""
        for ev in self._fwd_buf:
            self._emit(ev)
        self._sync()
        self._fwd_buf.clear()

    def _cancel_timer(self) -> None:
        if self._fwd_timer:
            self._fwd_timer.cancel()
            self._fwd_timer = None

    # ── Callback del temporizador (hilo Timer) ────────────────────────────────

    def _on_fwd_hold(self) -> None:
        """Se ejecuta cuando ADELANTE se mantiene el tiempo suficiente."""
        with self._lock:
            if not (self._fwd_pressed and not self._fwd_triggered):
                return
            self._fwd_triggered = True
            self._fwd_buf.clear()
        # Llamar al gesto fuera del lock (Popen es no bloqueante)
        gesture_screenshot()

    # ── Manejador de eventos de teclado/botones ───────────────────────────────

    def _handle_key(self, event) -> None:
        code, val = event.code, event.value

        # ── Botón ADELANTE (BTN_EXTRA = botón 8) ──────────────────────────
        if code == ecodes.BTN_EXTRA:
            if val == 1:                          # pulsación
                self._fwd_pressed   = True
                self._fwd_triggered = False
                self._fwd_buf       = [event]
                self._cancel_timer()
                self._fwd_timer = threading.Timer(
                    FORWARD_HOLD_TIME, self._on_fwd_hold
                )
                self._fwd_timer.start()

            elif val == 0:                        # liberación
                self._fwd_pressed = False
                self._cancel_timer()
                if self._fwd_triggered:
                    self._fwd_buf.clear()         # gesto consumió el evento
                else:
                    # Clic rápido → reenviar pulsación + liberación normalmente
                    self._replay_fwd()
                    self._emit(event)
                    self._sync()
                self._fwd_triggered = False
            return

        # ── Botón ATRÁS (BTN_SIDE = botón 9) ──────────────────────────────
        if code == ecodes.BTN_SIDE:
            if val == 1:                          # pulsación
                self._back_pressed   = True
                self._back_triggered = False
                self._back_press_ev  = event
                self._dx = 0
                self._dy = 0

            elif val == 0:                        # liberación
                self._back_pressed = False
                if not self._back_triggered:
                    # Sin gesto → reenviar clic normal como dos frames separados
                    # (press + SYN, luego release + SYN) igual que hace hardware real.
                    if self._back_press_ev is not None:
                        self._emit(self._back_press_ev)
                        self._sync()              # SYN tras press
                    self._emit(event)
                    self._sync()                  # SYN tras release
                # Si hubo gesto, los eventos fueron consumidos
                self._back_triggered = False
                self._back_press_ev  = None
            return

        # Cualquier otro botón → reenviar tal cual
        self._emit(event)
        self._sync()

    # ── Manejador de movimiento relativo ─────────────────────────────────────

    def _handle_rel(self, event) -> None:
        # Acumular movimiento si ATRÁS está pulsado y no hay gesto aún
        if self._back_pressed and not self._back_triggered:
            if event.code == ecodes.REL_X:
                self._dx += event.value
            elif event.code == ecodes.REL_Y:
                self._dy += event.value

            if abs(self._dx) + abs(self._dy) >= MOVEMENT_THRESHOLD:
                self._back_triggered = True
                self._back_press_ev  = None   # consumido

                abs_x, abs_y = abs(self._dx), abs(self._dy)

                if abs_y > abs_x and self._dy < 0:
                    # Movimiento dominante: ARRIBA
                    gesture_present_windows()
                elif abs_y > abs_x and self._dy > 0:
                    # Movimiento dominante: ABAJO
                    gesture_present_all_desktops()
                elif abs_x >= abs_y:
                    # Movimiento dominante: HORIZONTAL
                    # Efecto swipe: arrastrar a la derecha muestra el escritorio
                    # anterior (como deslizar contenido hacia la derecha), y
                    # arrastrar a la izquierda muestra el siguiente.
                    if self._dx > 0:
                        gesture_prev_desktop()   # swipe derecha → escritorio anterior
                    else:
                        gesture_next_desktop()   # swipe izquierda → escritorio siguiente

        # El cursor siempre se mueve con normalidad
        self._emit(event)
        self._sync()

    # ── Bucle principal ───────────────────────────────────────────────────────

    def run(self) -> None:
        log.info(
            "Daemon activo | ADELANTE (%.1fs)=captura | "
            "ATRÁS+ARRIBA=ventanas | ATRÁS+ABAJO=todos escritorios | ATRÁS+DERECHA/IZQ=escritorio | "
            "Ctrl-C / SIGTERM para salir.",
            FORWARD_HOLD_TIME,
        )
        try:
            for event in self._device.read_loop():
                if not self._running:
                    break
                with self._lock:
                    if event.type == ecodes.EV_KEY:
                        self._handle_key(event)
                    elif event.type == ecodes.EV_REL:
                        self._handle_rel(event)
                    # EV_SYN y otros tipos: gestionados inline o ignorados
        except OSError as exc:
            if self._running:
                log.error("Error de lectura del dispositivo: %s", exc)
        finally:
            self._cleanup()

    def stop(self) -> None:
        """Detiene el daemon desenganchando el bucle de lectura."""
        self._running = False
        # Cerrar el dispositivo provoca que read_loop() lance OSError y salga
        try:
            self._device.close()
        except OSError:
            pass

    def _cleanup(self) -> None:
        log.info("Apagando daemon.")
        self._cancel_timer()
        for obj in (self._device, self._ui):
            try:
                if obj is self._device:
                    obj.ungrab()
                obj.close()
            except OSError:
                pass

# ─────────────────────────────── Punto de entrada ─────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Daemon de gestos de ratón para KDE Plasma en Wayland.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                          # auto-detecta el ratón
  %(prog)s --device /dev/input/event5
  %(prog)s --list-devices           # lista ratones con botones laterales
  %(prog)s --detect                 # identifica tu ratón pulsando un botón (interactivo)
  %(prog)s --detect-once            # igual pero sale tras la primera detección
  %(prog)s --debug                  # logging detallado

Variables de entorno:
  MOUSE_DEVICE=/dev/input/eventX   # dispositivo a usar
  MGS_HOLD_TIME=0.4                # segundos para mantener ADELANTE
  MGS_MOVE_THRESHOLD=80            # píxeles para activar gesto de ATRÁS
""",
    )
    parser.add_argument(
        "--device", "-d",
        metavar="PATH",
        help="Ruta al dispositivo de entrada (p.ej. /dev/input/event5).",
    )
    parser.add_argument(
        "--list-devices", "-l",
        action="store_true",
        help="Lista los ratones físicos disponibles con botones laterales y sale.",
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help="Modo interactivo: pulsa un botón lateral para identificar tu ratón.",
    )
    parser.add_argument(
        "--detect-once",
        action="store_true",
        help="Igual que --detect pero sale tras la primera pulsación (útil para scripts).",
    )
    parser.add_argument(
        "--detect-timeout",
        type=float,
        default=30.0,
        metavar="SECS",
        help="Tiempo límite en segundos para --detect-once (por defecto: 30).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activa logging detallado.",
    )
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.list_devices:
        print_side_button_mice()
        return

    if args.detect:
        detect_interactive()
        return

    if args.detect_once:
        path = detect_once(timeout=args.detect_timeout)
        if path:
            # Solo la ruta a stdout para que el script de instalación la capture
            print(path)
            sys.exit(0)
        else:
            sys.exit(1)

    device_path = (
        args.device
        or os.environ.get("MOUSE_DEVICE")
        or find_side_button_mouse()
    )

    if not device_path:
        log.error(
            "No se encontró ningún ratón con botones laterales.\n"
            "  • Ejecuta con --list-devices para ver los dispositivos disponibles.\n"
            "  • Define MOUSE_DEVICE=/dev/input/eventX o usa --device PATH.\n"
            "  • Asegúrate de estar en el grupo 'input':\n"
            "      sudo usermod -aG input $USER   (luego cierra sesión y vuelve a entrar)"
        )
        sys.exit(1)

    # Advertir si qdbus no está disponible
    if QDBUS:
        log.info("D-Bus utility: %s", QDBUS)
    else:
        log.warning(
            "qdbus no encontrado. Los gestos de escritorio y ventanas no funcionarán.\n"
            "  sudo pacman -S qt6-tools"
        )

    service = MouseGestureService(device_path)

    def _sighandler(signum, _frame):
        log.info("Señal %d recibida, apagando.", signum)
        service.stop()

    signal.signal(signal.SIGTERM, _sighandler)
    signal.signal(signal.SIGINT,  _sighandler)

    service.run()


if __name__ == "__main__":
    main()
