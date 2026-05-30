# CachyOS — Postinstalación y Personalizazión

Guía personal para preparar y personalizar un entorno CachyOS a mi gusto. Establece un diseño de escritorio limpio y consistente, manteniendo la usabilidad. Contiene un listado de los programas que uso habitualmente y sus ajustes concretos. También se listan algunos scripts custom que me he creado para hacerme la vida más fácil y sincronizar ciertos servicios como Google Drive, OPRobots o Twitch.

## Índice

- [AUR](#aur)
- [FlatPak](#flatpak)
- [Personalización de Konsole y shell](#personalizacion-de-konsole-y-shell)
- [Wallpaper Engine (KDE)](#wallpaper-engine-kde)
- [Colores y Temas (Plasma y Kvantum)](#colores-y-temas-plasma-y-kvantum)
- [Fondo dinámico en inicio de sesión](#fondo-dinamico-en-inicio-de-sesion)
- [Gestión de ventanas](#gestion-de-ventanas)
- [PlatformIO y STLink — reglas udev](#platformio-y-stlink---reglas-udev)
- [Red y Firewall](#red-y-firewall)
- [Unidades de red (FailServer)](#unidades-de-red-failserver)
- [Particiones y otros Discos](#particiones-y-otros-discos)
- [F3D — Modo STEP y miniaturas](#f3d---modo-step-y-miniaturas)
- [Vivaldi](#vivaldi)
- [Brave](#brave)
- [VSCode](#vscode)
- [Emoji Picker: Pegado automático](#emoji-picker-pegado-automatico)
- [Gestos de ratón](#gestos-de-raton)
- [OBS](#obs)
- [MacroDeck](#macrodeck)
- [Google Drive con rclone](#google-drive-con-rclone)
- [BLHeliSuite](#blhelisuite)
- [Google Drive con rclone](#google-drive-con-rclone)
- [TeamViewer](#teamviewer)
- [GIT](#git)
- [GIT Large File System](#git-large-file-system)
- [Gaming](#gaming)
- [Solución de Problemas](#solucion-de-problemas)
- [Inicio Automático](#inicio-automatico)

---

## AUR

Instala los paquetes listados desde AUR con `paru -S`:

```bash
paru -S --sudoloop \
	brave-bin vivaldi discord blender freecad gimp inkscape kicad mypaint \
	qbittorrent kdenlive obs-browser obs-pipewire-audio-capture obs-3d-effect \
	obs-transition-table qt6-webengine vlc visual-studio-code-bin pulseview spotify \
	bazaar jdk-openjdk archlinux-java-run stm32cubemx orca-slicer f3d zsh fastfetch \
	cachyos-gaming-meta \ steam wallpaper-engine-kde-plugin-git kvantum xdotool \
	wl-clipboard ydotool rclone teamviewer git-lfs expresslrs-configurator-bin \
	prismlauncher
```

> [!NOTE]
> --sudoloop: Mantiene activa la autenticación de sudo durante toda la operación

Nota rápida: si `orca-slicer` falla en su versión normal, usa `orca-slicer-bin`.

## FlatPak

Instalar `Bottles` desde Flathub para ejecución de aplicaciones de Windows:

```bash
flatpak install flathub com.usebottles.bottles
```

## Personalización de Konsole y shell

Instalación y configuración rápida:

```bash
unzip -o ./assets/plasma6macos-fonts.zip -d ~/.local/share/fonts
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" -- --unattended
git clone https://github.com/zsh-users/zsh-autosuggestions ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-history-substring-search ~/.oh-my-zsh/custom/plugins/zsh-history-substring-search
curl -sS https://starship.rs/install.sh | sh
unzip -o ./assets/plasma6macos-zshstarship-konsole.zip -d ~
mkdir -p ~/.local/share/fastfetch
unzip -o ./assets/plasma6macos-fastfetch.zip "ascii/*" "presets/*" -d ~/.local/share/fastfetch/
```

Edita el fichero `~/.zshrc`

```bash
nano ~/.zshrc
```

Para mostrar información del PC al abrir una terminal añadiendo el siguiente contenido al final

```ini
if [[ $- == *i* ]] && [[ "$TERM_PROGRAM" != "vscode" ]]; then
	clear
	fastfetch --config sysinfo
fi
```

Edita `~/.config/starship.toml` para personalizar el prompt

```bash
nano ~/.config/starship.toml
```

Añade a la sección `[os.symbols]` la sección para CachyOS.

```ini
CachyOS = "󰣇"
```

> Es posible que no se vea el icono en GitHub

Comprueba el nuevo terminal

```bash
source ~/.zshrc
```

Accede a las preferencias de _Konsole_ y asegúrate que `zsh-starship` sea el _Perfil_ predeterminado

En VSCode configura el terminal por defecto a `zsh` y la fuente a `FiraCode Nerd Font Mono` para ver los iconos. (`~/.config/Code/User/settings.json`)

```json
"terminal.integrated.defaultProfile.linux": "zsh",
"terminal.integrated.fontFamily": "FiraCode Nerd Font Mono",
```

## Wallpaper Engine (KDE)

> [!IMPORTANT]
> Para que el plugin funcione puede ser necesario tener Wallpaper Engine instalado en Steam y activar la compatibilidad Windows 7 en las opciones del programa.

Ajusta los fondos de escritorio seleccionando la opción `Wallpaper Engine for Kde` en el desplegable de _Tipo de fondo_

Pulsa sobre `Library` para buscar la carpeta raíz de la librería de Steam. Debes seleccionar el directorio que contiene steamapps. `SteamLibrary` en este caso:

```
├── SteamLibrary
│   ├── steamapps
│   ├── libraryfolder.vdf
│   └── steam.dll
└── ...
```

Los fondos que tengas descargados en Wallpaper Engine (si está sincronizado) deberían aparecer automáticamente.

> [!TIP]
> En el apartado _Settings_ puedes establecer ajustes concretos del fondo. Es recomendable usar _Display: Scale and Dropp_ para que el fondo se ajuste correctamente al escritorio.

## Colores y Temas (Plasma y Kvantum)

### Tema Global

Instala y aplica el tema [Utterly-Nord](https://store.kde.org/p/2135625/) desde el apartado de Tema global en las preferencias.

> [!TIP]
> Puedes pulsar sobre _Obtener novedades_ y buscarlo o importar el fichero [Utterly-Nord](./assets/Utterly-Nord.tar.xz)

### Kvantum Manager: Estilo de las Aplicaciones

En el apartado _Instalar / Actualizar temas_, selecciona la carpeta con la extracción de [Utterly-Nord-kvantum](./assets/Utterly-Nord-kvantum.zip) y pulsa _Instalar_.

> [!TIP]
> También disponible en la [tienda de KDE](https://store.kde.org/p/1905813/)

En el apartado _Cambiar / borrar un tema_, selecciona `Utterly-Nord` y pulsa _Usar este team_

> [!IMPORTANT]
> Asegúrate que en el apartado de _Estilo de las aplicaciones_ esté seleccionado y aplicado el estilo _kvantum-dark_

### Decoraciones de las Ventanas

Instala y aplica el tema [Utterly Round Dark](https://store.kde.org/p/1901768/) desde el apartado de Decoraciones de las ventanas en las preferencias.

En este mismo apartado, ajusta en la parte superior el borda a _Sin bordes de ventana_

> [!TIP]
> Puedes pulsar sobre _Obtener novedades_ y buscarlo o importar el fichero [Utterly-Round-Desktop](./assets/Utterly-Round-Desktop.tar.xz)

### Iconos

Pulsa en _Obtener novedades_, busca el set de iconos `Tela` y selecciona y aplica el set _Tela Dark_

> [!IMPORTANT]
> En este punto, debes reiniciar el sistema para asegurar que todas las configuraciones se hayan aplicado correctamente.

### WindowButtons plasmoid

> [!WARNING]
> Por ahora esto no está funcionando correctamente, así que edita los elementos gráficos de la barra superior y elimina el componente _WindowButtons_

Este plasmoid sirve para mostrar los botones de la ventana (cerrar, maximizar, ...) en la barra superior.

```bash
sudo ./.local/share/plasma/plasmoids/org.kde.windowbuttons/lib-install.sh
kwriteconfig6 --file ~/.config/kwinrc --group Windows --key BorderlessMaximizedWindows false
qdbus6 org.kde.KWin /KWin reconfigure
```

### Fuentes (opcional)

Puedes instalar las siguiente fuentes desde el menú _Gestión de tipos de letra_, pulsando sobre _Instalar desde el archivo_

San Francisco Pro ([repositorio](https://github.com/sahibjotsaggu/San-Francisco-Pro-Fonts) y [assets](./assets/San-Francisco-Pro-Fonts.zip)) y SF Mono ([repositorio](https://github.com/supercomputra/SF-Mono-Font) y [assets](./assets/SF-Mono-Font.zip))

```bash
cd && sudo ./.local/share/plasma/plasmoids/org.kde.windowbuttons/lib-install.sh
```

## Fondo dinámico en inicio de sesión

Lanzar el script de generación de fondo dinámico

```bash
chmod +x ./scripts/dynamic-login-wallpaper.sh
./scripts/dynamic-login-wallpaper.sh
```

El script creará una imagen en `~/.dynamic-login-wallpaper/dynamic-login-wallpaper.png`. Esta imagen se establecerá como fondo desde la sección _Pantalla de inicio de sesión_.

> [!TIP]
> Cada vez que actualices el fondo de escritorio del Wallpaper Engine deberás ejecutar el script para que se actualice la imagen de fondo. La pantalla de login debería actualizarse automáticamente.

## Gestión de ventanas

- Activar en KWin scripts de escritorios virtuales solo en monitor principal.
- Instalar y activar el script KWin "Remember Window Positions" para restaurar ventanas.

## PlatformIO y STLink — reglas udev

PlatformIO:

```bash
curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/develop/platformio/assets/system/99-platformio-udev.rules | sudo tee /etc/udev/rules.d/99-platformio-udev.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

ST-Link:

```bash
sudo nano /etc/udev/rules.d/49-stlink-udev.rules
```

Añadir el siguiente contenido al fichero:

```ini
# ST-Link V2
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3748", MODE="0666"

# ST-Link V2-1
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="374b", MODE="0666"

# ST-Link V2.1 (en mi caso)
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3752", MODE="0666"

# ST-Link V3
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="374f", MODE="0666"
```

> [!NOTE]
> Es posible que haya dispositivos ST-Link con diferente _idVendor_ o _idProduct_

Recargar reglas tras editar:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Red y Firewall

Abrir puerto para MacroDeck (TCP 8191):

```bash
sudo ufw allow 8191/tcp
```

## Unidades de red (FailServer)

Montaje desde Dolphin:

1. Abre `smb://<LOCAL_IP_OR_HOSTNAME>` en Dolphin.
2. Accede por primera vez a algún directorio y guarda las credenciales
3. Luego, pulsa botón derecho y selecciona "Añadir a Lugares" para montarlo automáticamente de ahora en adelante.

## Particiones y otros Discos

Comprueba las particiones y discos para obtener su UUID:

```bash
lsblk -f
```

Edita el fichero fstab para montar automáticamente las unidades al iniciar

```bash
sudo nano /etc/fstab
```

Añade al final del fichero las configuraciones que correspondan

```ini
# storage
UUID=<UUID_STORAGE>  /mnt/storage  btrfs  defaults,noatime,compress=zstd:3  0  0

# OPRobots
UUID=<UUID_OPROBOTS>  /mnt/OPRobots ntfs3  rw,user,exec,uid=<UID>,gid=<GID>,noatime  0  0

# NobaraOS
UUID=<UUID_NOBARA>  /mnt/NobaraOS  btrfs  defaults,noatime  0  0
```

> [!TIP]
> Para obtener tu UID y GID puedes ejecutar `id -u` e `id -g` respectivamente en una terminal

Verificar montajes antes de reiniciar:

```bash
sudo mount -a
```

> [!IMPORTANT]
> Si reinicias sin comprobar si no hay errores, puede que el sistema entre en "modo emergencia"

## F3D — Modo STEP y miniaturas

Crear un lanzador que fuerce lectura STEP:

```bash
cp /usr/share/applications/f3d.desktop ~/.local/share/applications/f3d-step.desktop
nano ~/.local/share/applications/f3d-step.desktop
```

Dentro del `.desktop`, añade o modifica:

```ini
Exec=f3d --force-reader=STEP %F
Name=F3D STEP Viewer
```

Actualizar la base de datos de aplicaciones:

```bash
update-desktop-database ~/.local/share/applications
```

Miniaturas para STEP (thumbnailer):

```bash
mkdir -p ~/.local/share/thumbnailers
cp /usr/share/thumbnailers/f3d-plugin-occt.thumbnailer ~/.local/share/thumbnailers/
nano ~/.local/share/thumbnailers/f3d-plugin-occt.thumbnailer
```

Dentro del archivo `*.thumbnailer` ajusta `Exec=` así:

```ini
Exec=f3d --config=thumbnail --load-plugins=occt --force-reader=STEP --verbose=quiet --output=%o --resolution=%s,%s %i
```

Forzar regeneración de miniaturas y reiniciar Dolphin:

```bash
rm -rf ~/.cache/thumbnails/*
kquitapp6 dolphin || true
dolphin &
```

> [!NOTE]
> Es necesario activar las miniaturas para los tipos de ficheros necesarios; en mi caso todos

## Vivaldi

- Cambia el icono de Descargas a "Barra de Direcciones" para evitar el panel lateral.
- En Apariencia, elige "Usar ventana nativa" para una mejor integración con KDE y el tema custom.
- Limpia la barra lateral dejando solo servicios de chat IA ([Copilot](https://github.com/copilot), [ChatGPT](https://chatgpt.com/c/), [Gemini](https://gemini.google.com/app?hl=es-ES)) y servicios de mensajería ([Telegram](https://web.telegram.org/k/), [WhatsApp](https://web.whatsapp.com/))

> [!TIP]
> Para que funcione WhatsApp es necesario activar el modo de visualización del panel y navegar al _home_ para que se muestre el QR de inicio de sesión

## Brave

- Cambia en el apartado _Aspecto_ al tema QT y activa _Usar bordes y barra de título_ para mejor integración con KDE y tema custom.

## VSCode

Modifica los argumentos del lanzador con el programa _Editor del menu_ para que use X11 en lugar de Wayland

```ini
--enable-features=UseOzonePlatform --ozone-platform=x11 %F
```

> [!TIP]
> Edita directamente el lanzador de `/usr/share/applications/code.desktop` para aplicar los cambios también a la acción "Abrir nueva ventana"

De esta forma VSCode respetará el diseño de botones y menús y será más compatible con aplicaciones X11 (zoom-to-mouse de OBS, por ejemplo)

## Emoji Picker: Pegado automático

Crea un nuevo servicio para `ydotoold`

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/ydotoold.service
```

Con el siguiente contenido

```ini
[Unit]
Description=ydotool daemon

[Service]
ExecStart=/usr/bin/ydotoold --socket-path=/run/user/<UID>/.ydotool_socket
Restart=on-failure

[Install]
WantedBy=default.target
```

Lanza el nuevo servicio y comprueba su estado para verificar que esté activo

```bash
systemctl --user daemon-reload
systemctl --user enable --now ydotoold
systemctl --user status ydotoold
```

> [!TIP]
> Si el servicio no arranca correctamente, cierra cualquier otra instancia previa de `ydotoold`, reinicia la sesión y vuelve a intentarlo.
> Para obtener tu UID puedes ejecutar `id -u` en la terminal

Configura un nuevo atajo _Atajos Personalizados_ que ejecute el script [emoji-picker.sh](./scripts/emoji-picker.sh).

## Gestos de ratón

Daemon que convierte gestos del ratón en atajos de teclado de KDE Plasma, usando los botones laterales **Adelante** y **Atrás** como modificadores. Los botones siguen funcionando con normalidad cuando no activan un gesto.

| Gesto | Acción |
|---|---|
| Mantener **Adelante** (≥ 0,4 s) | Captura de pantalla (selección de región) |
| **Atrás** + mover **arriba** | Mosaico de ventanas del escritorio actual |
| **Atrás** + mover **abajo** | Preview de todos los escritorios virtuales |
| **Atrás** + mover **derecha** | Escritorio virtual anterior |
| **Atrás** + mover **izquierda** | Escritorio virtual siguiente |

Consulta la [guía completa de instalación y uso](./scripts/mouse-gestures/README.md).

## OBS

Edita los argumentos del lanzador en `~/.local/share/applications/` para dar compatibilidad con la interfaz gráfica y las fuentes necesarias

```ini
__NV_DISABLE_EXPLICIT_SYNC=1, QT_QPA_PLATFORM=xcb
```

Activa el servidor WebSocket en el desplegable de Herramientas

## MacroDeck

En la aplicación de Bottles, accede al menú de _Importar_ y selecciona _Archivo completo_ en la esquina superior izquierda para importar el fichero [MacroDeck-backup](./assets/MacroDeck-backup.tar.gz) y restaurar la Bottle.

Abre MacroDeck y configura el plugin de conexión con OBS. Debería bastar con actualizar la contraseña.

Añade Macro Deck 2 al directorio de inicio automático copiando su lanzador de `~/.local/share/applications/` a `~/.config/autostart/`

## BLHeliSuite

En la aplicación de Bottles, accede al menú de _Importar_ y selecciona _Archivo completo_ en la esquina superior izquierda para importar el fichero [BLHeliSuite-backup](./assets/BLHeliSuite-backup.tar.gz) y restaurar la Bottle.

Crea un nuevo lanzador para la Bottle de BLHeliSuite

```bash
nano ~/.local/share/applications/blhelisuite.desktop
```

Con el siguiente contenido:

```ini
[Desktop Entry]
Comment=Launch BLHeliSuite using Bottles (update COM ports if needed).
Exec="$HOME/Scripts/CachyOS Customization/scripts/blheli-suite-port-sharing.sh"
Icon="$HOME/.var/app/com.usebottles.bottles/data/bottles/bottles/BLHeli-Suite/icons/icon_promo.png"
Name=BLHeliSuite
NoDisplay=false
Path=
PrefersNonDefaultGPU=false
StartupNotify=true
StartupWMClass=BLHeliSuite
Terminal=false
TryExec=/var/lib/flatpak/exports/bin/com.usebottles.bottles
Type=Application
X-Flatpak=com.usebottles.bottles
X-KDE-SubstituteUID=false
```

Actualiza la base de datos de aplicaciones para que el nuevo lanzador esté disponible

```bash
update-desktop-database ~/.local/share/applications
```

> [!NOTE]
> Asegúrate de que el script `blheli-suite-port-sharing.sh` tenga permisos de ejecución (`chmod +x blheli-suite-port-sharing.sh`).
> Es posible que sea necesario actualizar la ruta de la imagen del icono para usar ruta absoluta sin variable de entorno `$HOME` para que se muestre correctamente en el lanzador.

## Google Drive con `rclone`

1. Crear credenciales en Google Cloud Console (resumen paso a paso):

- Ve a https://console.cloud.google.com/ y crea un proyecto nuevo (ej.: _CachyOS-rclone_).
- En la barra de búsqueda superior, busca _Google Drive API_ y dale a _Habilitar_.
- Ve a _Pantalla de consentimiento de OAuth_ en _APIs y servicios_, selecciona tipo de usuario _Externo_, ponle un nombre y guarda (no necesitas rellenar más datos).
- En la sección _Usuarios de prueba_ dentro de _Público_, añade la cuenta de Gmail que vas a usar para autorizar (tu correo personal).
- Ve a _Clientes_ y pulsa en _Crear cliente_. Selecciona tipo de aplicación: Aplicación de escritorio (Desktop app) y haz clic en Crear.
- Copia el `Client ID` y `Client Secret` que genera Google.

2. Configurar sincronización:

```bash
rclone config
```

- `n` para nuevo remoto
- Nombre: `gdrive` (o el que prefieras).
- Tipo de almacenamiento: selecciona `drive` (Google Drive).
- Cuando pregunte `client_id` y `client_secret` pega los valores generados.
- `scope`: opciones comunes:
  - `drive`: acceso completo recomendado si quieres sincronizar todo.
  - `drive.readonly`: solo lectura.
  - `drive.file`: acceso limitado a archivos creados por la app.
  - `drive.appfolder`: carpeta de aplicación dedicada.
    Elige `drive` (1) para sincronizaciones completas.
- `root_folder_id`: dejar en blanco salvo que quieras apuntar a un Shared Drive o carpeta concreta.
- `service_account_file`: dejar en blanco para autenticación por OAuth.
- `Edit advanced config?`: `n` salvo que necesites configurar proxies u opciones especiales.
- `Use auto config?`: `y` Se abrirá el navegador y te pedirá autorización.
- Confirma que todo está bien con `y` y sal del configurador con `q`.

3. Compartido conmigo:

Si tienes carpetas en _Compartido conmigo_, añádelas a _Mi unidad_ como accesos directos en la web de Google Drive antes de sincronizar. `rclone` puede tener problemas con elementos que solo están en _Compartido conmigo_ si no los conviertes en accesos directos dentro de _Mi unidad_.

4. Sincronización inicial con `bisync`:

```bash
mkdir -p ~/GoogleDrive
rclone bisync gdrive: ~/GoogleDrive \
	--resync \
	--drive-skip-gdocs \
	--drive-skip-dangling-shortcuts \
	--compare size,modtime,checksum \
	--resilient -vP
```

Opciones usadas:

- `bisync`: intenta mantener ambos lados (local y drive) en sync. Puede eliminar archivos si detecta que han sido borrados en el origen; úsalo con precaución.
- `--resync`: fuerza una sincronización completa, útil para la primera ejecución.
- `--drive-skip-gdocs`: evita que `rclone` trate de descargar/convertir Google Docs/Sheets/Slides nativos.
- `--drive-skip-dangling-shortcuts`: omite accesos directos que apuntan a elementos inexistentes.
- `--compare size,modtime,checksum`: compara por tamaño, fecha de modificación y checksum para detectar cambios con mayor fiabilidad.
- `--resilient`: intenta continuar ante errores transitorios y reintentos.
- `--drive-acknowledge-abuse`: ermite operar sobre ficheros marcados por Google como abuso/maliciosos; usar con precaución.
- `-vP`: mostrar información del proceso y progreso.

5. Sincronización periódica con servicio `systemd` y temporizador:

Crea el script de sincronización

```bash
nano ~/.local/bin/rclone_sync.sh
```

Y añade el siguiente contenido

```bash
#!/bin/bash
if pidof -o %PPID -x "$0"; then
	exit 1
fi

rclone bisync gdrive: "$HOME/GoogleDrive" \
	--drive-skip-gdocs --drive-skip-dangling-shortcuts \
	--drive-acknowledge-abuse --compare size,modtime,checksum --resilient
```

Crea el servicio

```bash
nano ~/.config/systemd/user/rclone-sync.service
```

Y añade el siguiente contenido

```ini
[Unit]
Description=Sincronizacion optimizada de Rclone con Google Drive
After=network-online.target

[Service]
Type=oneshot
ExecStart=%h/.local/bin/rclone_sync.sh

[Install]
WantedBy=default.target
```

Crea el temporizador

```bash
nano ~/.config/systemd/user/rclone-sync.timer
```

Con el siguiente contenido

```ini
[Unit]
Description=Temporizador para la sincronizacion de Rclone

[Timer]
OnBootSec=5m
OnUnitActiveSec=20m
Persistent=true

[Install]
WantedBy=timers.target
```

> Se ejecutará el script de sincronizazión cada 20 minutos, esperando 5 minutos después del inicio del sistema

Activar y usar:

```bash
chmod +x ~/.local/bin/rclone_sync.sh
systemctl --user daemon-reload
systemctl --user enable --now rclone-sync.timer
```

> [!TIP]
> Lista completa de los timers configurados y su próximo tiempo de ejecución: `systemctl --user list-timers --all`
> Logs en tiempo real del proceso: `journalctl --user -u rclone-sync.service -f`
> Forzar sincronización manual en cualquier momento: `systemctl --user start rclone-sync.service`

## TeamViewer

Inicia el proceso en segundo plano

```bash
teamviewer --daemon start
```

Configúralo para que se inicie automáticamente con el sistema

Añade el dispositivo a la cuenta para permitir conexión desatendida

## GIT

Configura tu usuario y correo electrónico para GIT

```bash
git --global config user.name xxxxx
git --global config user.email xxxxx
git config --global init.defaultBranch main
```

## GIT Large File Storage

Inicia _lfs_ en el directorio de git que necesites

```bash
git lfs install
```

Añade todos los tipos de fichero que quieras gestionar por LFS y añade `.gitattributes` al control de versiones

```bash
git lfs track "*.zip"
git lfs track "*.tar.gz"
git lfs track "*.tar.xz"
git add .gitattributes
```

## Gaming

Usa `Proton Experimental` en Steam cuando necesites compatibilidad.

## Solución de Problemas

### Conflicto de plugins en CachyUpdate (vlc-plugin-lua vs vlc-plugin-luajit)

Durante una actualización del sistema puede aparecer un conflicto entre `vlc-plugin-lua` y `vlc-plugin-luajit` que impide continuar con el update ni desinstalar el paquete en conflicto de forma normal.

La solución es eliminar el paquete conflictivo ignorando las dependencias y luego continuar con la actualización:

```bash
sudo pacman -Rdd vlc-plugin-luajit
sudo pacman -Syu
```

> [!WARNING]
> El flag `-dd` omite la comprobación de dependencias al desinstalar. Úsalo solo cuando sea estrictamente necesario y tengas claro qué paquete está causando el conflicto.

## Inicio Automático

> [!TIP]
> La ruta en la que se almacenan los lanzadores de inicio automático es `~/.config/autostart/`
> Los lanzadores `*.desktop` se almacenan en `~/.local/share/applications/` o `/usr/share/applications/` si están instaladas globalmente

Editar el lanzador de Steam con `Exec=/usr/bin/steam -silent %U` para que inicie ya minimizado.
