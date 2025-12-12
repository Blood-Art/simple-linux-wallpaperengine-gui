# Wallpaper Engine GUI

GUI for managing Wallpaper Engine wallpapers on Linux.

## Dependencies

### System Requirements

**linux-wallpaperengine:**
```bash
# Arch/Manjaro
yay -S linux-wallpaperengine

# Ubuntu/Debian/Fedora - build from source:
git clone https://github.com/Almamu/linux-wallpaperengine.git
cd linux-wallpaperengine
mkdir build && cd build
cmake ..
make
sudo make install
```

**Monitor detection (choose one):**
```bash
# X11
sudo pacman -S xorg-xrandr        # Arch
sudo apt install x11-xserver-utils # Ubuntu/Debian
sudo dnf install xrandr            # Fedora

# Wayland (wlroots: Sway, River, etc.)
sudo pacman -S wlr-randr          # Arch
sudo apt install wlr-randr        # Ubuntu/Debian
sudo dnf install wlr-randr        # Fedora

# Hyprland - hyprctl is already included
```

### Python Dependencies

```bash
pip install pillow pystray
```

Or via package manager:
```bash
# Arch/Manjaro
sudo pacman -S python-pillow python-pystray

# Ubuntu/Debian
sudo apt install python3-pil python3-pil.imagetk python3-tk
pip install pystray

# Fedora
sudo dnf install python3-pillow python3-pillow-tk python3-tkinter
pip install pystray
```

## Usage

```bash
python3 wallpaper_gui.py
```

Or:
```bash
chmod +x wallpaper_gui.py
./wallpaper_gui.py
```

## 

## Features

- Wallpaper settings (audio, FPS, scaling)

- Local wallpaper browser from Steam Workshop

- Multi-monitor support (X11 and Wayland)

- Multi-language support (6 languages)

  
