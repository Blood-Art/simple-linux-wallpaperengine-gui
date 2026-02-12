{
  pkgs ? import <nixpkgs> {system = "x86_64-linux";},
  lib,
}:
pkgs.stdenv.mkDerivation rec {
  name = "simple-linux-wallpaperengine-gui";
  src = ./.;
  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  propagatedBuildInputs = with pkgs; [
    (python3.withPackages (pythonPackages:
      with pythonPackages; [
        pyqt6
        pillow
        packaging
      ]))
    # (callPackage ../linux-wallpaperengine {})
    libxcb-cursor
  ];

  installPhase = ''
    mkdir -p $out/bin
    cp -r ./locales $out/bin
    install -Dm755 ./wallpaper_gui.py $out/bin/simple-linux-wallpaperengine-gui
    # wrapProgram $out/bin/simple-linux-wallpaperengine-gui \
    #   --prefix PATH : ${lib.makeBinPath propagatedBuildInputs}
  '';

  meta = {
    description = "Simple Linux Wallpaper Engine GUI";
    homepage = "https://github.com/Maxnights/simple-linux-wallpaperengine-gui";
    # license = licenses.gpl3;
    platforms = ["x86_64-linux"];
  };
}
