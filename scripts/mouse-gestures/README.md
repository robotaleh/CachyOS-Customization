# Mouse Gesture Shortcuts

Daemon que convierte gestos del ratón en acciones de KDE Plasma en Wayland, usando los botones laterales **Adelante** y **Atrás** como modificadores.

## Gestos disponibles

| Gesto | Acción |
|---|---|
| Mantener **Adelante** (≥ 0,4 s) | Captura de pantalla — abre Spectacle en modo selección de región |
| **Atrás** + mover ratón **arriba** | Mosaico de ventanas del escritorio actual |
| **Atrás** + mover ratón **abajo** | Preview de todos los escritorios virtuales |
| **Atrás** + mover ratón **a la derecha** | Escritorio virtual anterior |
| **Atrás** + mover ratón **a la izquierda** | Escritorio virtual siguiente |

> Los gestos de escritorio virtual funcionan igual que `Ctrl + Super + ←/→`: se detienen en el primer y último escritorio, sin salto circular.

### Comportamiento del passthrough

Los botones **Adelante** y **Atrás** siguen funcionando con normalidad cuando no activan un gesto:

- Un **clic rápido** de Adelante sigue siendo el botón de avanzar del navegador / explorador de archivos.
- Un **clic rápido** de Atrás sigue siendo el botón de retroceder.
- El cursor siempre se mueve con normalidad, incluso mientras se acumula el movimiento para un gesto.

---

## Arquitectura

```
Ratón físico (evdev, grab exclusivo)
        │
        ▼
mouse-gesture-shortcuts (daemon Python)
        │
        ├─── Gesto detectado ──► Acción KDE vía D-Bus (qdbus6 / kglobalaccel)
        │
        └─── Sin gesto (clic normal / movimiento) ──► UInput virtual (passthrough)
                                                              │
                                                              ▼
                                              KWin / Wayland compositor
                                              (ve un ratón normal)
```

El daemon captura el dispositivo físico en exclusiva (`grab()`), lo que garantiza que los eventos no llegan a ningún otro programa hasta que el daemon decide reenviarlos. El dispositivo UInput virtual es el que el compositor ve como el ratón en uso.

---

## Instalación

### Requisitos

| Paquete | Función |
|---|---|
| `python-evdev` | Leer eventos raw del ratón y crear el dispositivo UInput |
| `qt6-tools` | Proporciona `qdbus6`, necesario para invocar acciones de KDE |
| `spectacle` | Captura de pantalla (normalmente ya instalado en KDE) |

El script de instalación comprueba e instala lo que falte automáticamente.

### Pasos

```bash
cd scripts/mouse-gestures
chmod +x install.sh
./install.sh
```

El script realiza estos pasos en orden:

1. **Para el servicio** si ya está en ejecución (evita conflictos con el grab del ratón).
2. **Verifica e instala** dependencias (`python-evdev`, `qt6-tools`).
3. **Añade el usuario al grupo `input`** si no pertenece a él — necesario para acceder a `/dev/input/`. Si lo hace, pide cerrar sesión y volver a entrar antes de continuar.
4. **Instala la regla udev** para `/dev/uinput` (permite crear el dispositivo de passthrough sin root).
5. **Instala el daemon** en `/usr/local/bin/mouse-gesture-shortcuts`.
6. **Instala el servicio systemd** de usuario en `~/.config/systemd/user/`.
7. **Detecta el ratón** automáticamente:
   - Si hay un único candidato, lo selecciona sin preguntar.
   - Si hay varios, muestra un prompt interactivo: pulsa Adelante o Atrás en tu ratón para identificarlo.
   - Si ya existía una configuración de una instalación anterior, pregunta si deseas reconfigurar.
8. **Activa y arranca** el servicio.

> [!IMPORTANT]
> Si el script para en el paso 3 pidiendo cerrar sesión, hazlo, inicia sesión de nuevo y vuelve a ejecutar `bash install.sh`. El resto de pasos se completarán solos.

---

## Ajuste de sensibilidad

La configuración del dispositivo y la sensibilidad se guarda en un **drop-in de systemd** para no mezclarla con el archivo de servicio principal:

```
~/.config/systemd/user/mouse-gesture-shortcuts.service.d/device.conf
```

Contenido de ejemplo:

```ini
[Service]
# Dispositivo del ratón (ruta estable by-id, generado automáticamente por install.sh)
Environment=MOUSE_DEVICE=/dev/input/by-id/usb-0000_0000-event-mouse

# Segundos que hay que mantener pulsado Adelante para activar la captura
# Valores más bajos = más sensible (puede activarse sin querer)
Environment=MGS_HOLD_TIME=0.4

# Píxeles de desplazamiento acumulado para activar un gesto de Atrás
# Valores más altos = hay que mover más el ratón antes de que se active
Environment=MGS_MOVE_THRESHOLD=80
```

Tras editar el fichero, recarga y reinicia el servicio:

```bash
systemctl --user daemon-reload
systemctl --user restart mouse-gesture-shortcuts
```

---

## Comandos útiles

```bash
# Ver el estado del servicio
systemctl --user status mouse-gesture-shortcuts

# Ver los logs en tiempo real
journalctl --user -u mouse-gesture-shortcuts -f

# Reiniciar (después de cambios de configuración)
systemctl --user restart mouse-gesture-shortcuts

# Listar los ratones detectados con botones laterales
mouse-gesture-shortcuts --list-devices

# Identificar tu ratón de forma interactiva (pulsa un botón lateral)
mouse-gesture-shortcuts --detect-once

# Modo diagnóstico con logging detallado
mouse-gesture-shortcuts --debug
```

---

## Desinstalación

```bash
chmod +x uninstall.sh
./uninstall.sh
```

Elimina el servicio, el daemon y la regla udev. El usuario permanece en el grupo `input` (quitarlo requiere cerrar sesión); el script avisa de cómo hacerlo si lo deseas.

---

## Solución de problemas

### Los botones del ratón no funcionan como de costumbre

Comprueba que el servicio está activo y que el passthrough funciona:

```bash
journalctl --user -u mouse-gesture-shortcuts -n 30 --no-pager
```

Busca errores relacionados con UInput o permisos en `/dev/uinput`. Si aparece un error de permisos, vuelve a ejecutar `install.sh` para que instale la regla udev.

### El gesto de escritorio no para en el primer/último escritorio

Asegúrate de que `qdbus6` está instalado (`which qdbus6`). El daemon lo usa para invocar el shortcut de KWin directamente, que respeta los bordes. Si usas una versión antigua de qt6-tools, prueba `qdbus` en su lugar — el daemon lo detecta automáticamente.

### No se detecta el ratón al arrancar

El daemon utiliza rutas estables (`/dev/input/by-id/*`) que persisten entre reinicios y desconexiones USB. Si el ratón no está disponible al arrancar, el daemon reinenta automáticamente cada 5 segundos. Cuando el ratón reaparece, se reconecta sin intervención manual.

Si la configuración no se aplicó correctamente:
- Vuelve a ejecutar `install.sh` para que se vuelva a detectar el ratón y guarde su ruta estable.
- Comprueba la configuración actual: `cat ~/.config/systemd/user/mouse-gesture-shortcuts.service.d/device.conf`

### Desconexión prolongada (horas/reboot)

El daemon espera automáticamente a que el ratón reaparezca:
- Si desconectas el ratón y lo reconectas después de horas o tras un reboot, el daemon lo detecta y vuelve a monitorizarlo sin reinicio de servicio.
- Los logs muestran: `"Esperando a que el ratón vuelva a estar disponible..."` cuando el dispositivo no está presente.

Para verificar este comportamiento:
```bash
# Ver que el daemon está esperando
journalctl --user -u mouse-gesture-shortcuts -f

# Desconecta/Reconecta el ratón — el daemon reenconectará automáticamente
```

### El servicio no arranca con la sesión gráfica

Comprueba que la sesión de Plasma exporte correctamente `DBUS_SESSION_BUS_ADDRESS`:

```bash
systemctl --user show-environment | grep DBUS
```

Si está vacío, añade `systemd-xdg-autostart-generator` o configura el inicio desde _Preferencias del sistema → Inicio y apagado → Inicio automático_.
