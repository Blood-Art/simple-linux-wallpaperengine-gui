#!/bin/bash


install_system_deps() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        echo "Cannot detect OS. Please install Python 3 and venv manually."
        exit 1
    fi

    echo "Detected OS: $OS"
    
    case $OS in
        ubuntu|debian|pop|linuxmint|kali)
            echo "Installing dependencies for Debian/Ubuntu based systems..."
            sudo apt update
            # Added libxcb-cursor-dev per troubleshooting reports (fixes Qt xcb load error on Mint 22.3+)
            sudo apt install -y python3 python3-venv python3-pip git libxcb-cursor-dev
            ;;
        fedora|rhel|centos)
            echo "Installing dependencies for Fedora based systems..."
            sudo dnf install -y python3 python3-pip git
            ;;
        arch|manjaro|endeavouros|cachyos)
            echo "Installing dependencies for Arch based systems..."
            sudo pacman -Sy --noconfirm python python-pip git
            ;;
        *)
            echo "Unsupported or unknown distribution: $OS"
            echo "Please ensure Python 3, pip, and venv are installed."
            read -p "Press Enter to continue or Ctrl+C to abort..."
            ;;
    esac
}

echo "---------------------------------------"
echo " Simple Linux WallpaperEngine GUI Setup"
echo "---------------------------------------"


install_system_deps


if ! command -v linux-wallpaperengine &> /dev/null; then
    echo "Warning: 'linux-wallpaperengine' backend not found in PATH."
    
    # Check if it exists in the common /opt location mentioned in troubleshooting
    if [ -f "/opt/linux-wallpaperengine/linux-wallpaperengine" ] || [ -f "/opt/linux-wallpaperengine/bin/linux-wallpaperengine" ]; then
        echo "Found linux-wallpaperengine in /opt/linux-wallpaperengine, but it is not in your PATH."
        echo "You can temporarily fix this by running:"
        echo "  export PATH=\$PATH:/opt/linux-wallpaperengine"
        echo "Or add it to your ~/.profile for a permanent fix."
    else
        echo "This GUI requires the backend to function."
        echo "Please check the README.md for installation instructions."
    fi
    sleep 2
fi


echo "Setting up Python virtual environment..."

if [ -d ".venv" ]; then
    rm -rf .venv
fi

python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "Error creating virtual environment."
    exit 1
fi

source .venv/bin/activate


echo "Installing Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

chmod +x run_gui.sh

echo "---------------------------------------"
echo "Installation Complete!"
echo "Run the app using: ./run_gui.sh"
echo "---------------------------------------"
