# Simple Linux Wallpaper Engine GUI

A modern, universal GUI for [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine).

I encountered various problems on GNOME and KDE. I recommend using Linux Wallpaper Engine on tiling window managers such as i3, hyprland, and bspwm. </font> For KDE, I recommend trying this [plugin](https://github.com/catsout/wallpaper-engine-kde-plugin#build-and-install)


## Screenshots
<img width="2560" height="1440" alt="Pasted image" src="https://github.com/user-attachments/assets/15c6dc78-f51b-4c1b-aeb1-f2bad88bc898" />
<img width="2560" height="1440" alt="Pasted image (2)" src="https://github.com/user-attachments/assets/d36990b8-641a-44fe-b4ff-ca582d9494da" />



## Installation (Arch Linux / Manjaro)

The easiest way is to install via AUR. This will automatically install the backend (`linux-wallpaperengine`) and all dependencies.

```bash
yay -S simple-linux-wallpaperengine-gui-git
```

## 1. Prerequisites (The Backend)
This is just a GUI. You **must** install the core backend engine first. If you installed my GUI from AUR, then the main backend engine from Almamu(https://github.com/Almamu/linux-wallpaperengine) comes as a dependency. So you can skip this step.

### Arch / Manjaro
```bash
yay -S linux-wallpaperengine
```

### Debian / Ubuntu / Fedora (Build from Source)
Detailed instructions are [here](https://github.com/Almamu/linux-wallpaperengine#compiling), but essentially:
```bash
# Install build tools (Debian/Ubuntu)
sudo apt install build-essential cmake libx11-dev libxrandr-dev liblz4-dev

# Install build tools (Fedora)
sudo dnf install cmake gcc-c++ libX11-devel libXrandr-devel lz4-devel

# Clone & Build
git clone https://github.com/Almamu/linux-wallpaperengine.git
cd linux-wallpaperengine && mkdir build && cd build
cmake ..
make
sudo make install
```

## 2. Installation (The GUI)

This one-step script installs Python dependencies, and sets up the app.

```bash
git clone https://github.com/Maxnights/simple-linux-wallpaperengine-gui.git
cd simple-linux-wallpaperengine-gui
chmod +x install.sh
./install.sh
```

## 3. Usage

Start the application:

```bash
./run_gui.sh
```


## Troubleshooting

**"linux-wallpaperengine not found"**  
Ensure you completed Step 1. Run `linux-wallpaperengine --help` in a terminal to verify it's installed globally.

**Wallpapers not showing?**  
Go to the **Library** tab and click **Scan Local Wallpapers**. The app searches standard paths including `~/.local/share/Steam`, `~/.var/app/com.valvesoftware.Steam`, and `~/snap/steam`.



