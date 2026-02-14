{
  pkgs ? import <nixpkgs> {system = "x86_64-linux";},
  lib,
}:
pkgs.stdenv.mkDerivation rec {
  name = "simple-wallpaper-engine";
  src = pkgs.fetchFromGitHub {
    owner = "aarya-a-patel";
    repo = "simple-linux-wallpaperengine-gui";
    rev = "2847dd47a1fe3827f08625165d42d6ddb385d7f6";
    sha256 = "sha256-dE0irLqCEngqqH7K0y+0Z3RA+vquzSesOHbX9Xf7f+g=";
  };

  nativeBuildInputs = [pkgs.makeWrapper] ++ lib.optionals pkgs.stdenv.isLinux [pkgs.copyDesktopItems];

  propagatedBuildInputs = with pkgs; [
    (python3.withPackages (pythonPackages:
      with pythonPackages; [
        pyqt6
        pillow
        packaging
      ]))
    linux-wallpaperengine
    libxcb-cursor
  ];

  installPhase = ''
    mkdir -p $out/bin
    cp -r ./locales $out/bin
    install -Dm755 ./wallpaper_gui.py $out/bin/simple-wallpaper-engine
    wrapProgram $out/bin/simple-wallpaper-engine \
      --prefix PATH : ${lib.makeBinPath propagatedBuildInputs}
    mkdir -p $out/share/applications
    cp ${desktopItem}/share/applications/*.desktop \
       $out/share/applications/
  '';

  desktopItem = pkgs.makeDesktopItem {
    name = "simple-wallpaper-engine";
    desktopName = "Simple Wallpaper Engine";
    comment = "A modern GUI for linux-wallpaperengine";
    exec = "simple-wallpaper-engine";
    icon = "preferences-desktop-wallpaper";
    terminal = false;
    type = "Application";
    categories = ["Utility" "Settings" "DesktopSettings" "Qt"];
    keywords = ["wallpaper" "engine" "background" "steam"];
    startupNotify = true;
  };

  meta = {
    description = "Simple Linux Wallpaper Engine GUI";
    homepage = "https://github.com/Maxnights/simple-linux-wallpaperengine-gui";
    license = lib.licenses.gpl3;
    platforms = ["x86_64-linux"];
    mainProgram = "simple-wallpaper-engine";
  };
}
