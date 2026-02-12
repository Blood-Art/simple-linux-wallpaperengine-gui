{
  description = "simple-linux-wallpaperengine-gui devshell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {inherit system;};

    pythonEnv = pkgs.python3.withPackages (ps:
      with ps; [
        pyqt6
        pillow
        packaging
      ]);
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = [
        pythonEnv
        pkgs.libxcb-cursor
        pkgs.makeWrapper
      ];

      shellHook = ''
        echo "Dev shell ready."
        echo "Run: python3 ./wallpaper_gui.py"
      '';
    };
  };
}
