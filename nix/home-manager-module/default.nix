flake: {
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.programs.simple-wallpaper-engine;
  pkg = flake.packages.${pkgs.stdenv.hostPlatform.system}.default;
in {
  options.programs.simple-wallpaper-engine = {
    enable = lib.mkEnableOption "Wallpaper Engine Service";
    xdgAutostart = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Enable XDG autostart entry";
    };
  };

  config = lib.mkIf cfg.enable ({
      home.packages = [pkg];
    }
    // (lib.mkIf cfg.xdgAutostart {
      xdg.autostart = {
        enable = true;
        entries = [
          "${pkg}/share/applications/simple-wallpaper-engine.desktop"
        ];
      };
    }));
}
