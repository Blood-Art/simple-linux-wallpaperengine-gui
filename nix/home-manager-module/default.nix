flake: {
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.programs.simple-wallpaper-engine;
in {
  options.programs.simple-wallpaper-engine = {
    enable = lib.mkEnableOption "Wallpaper service (user systemd)";
    xdg-autostart = lib.mkEnableOption "Wallpaper service (user systemd)";
  };

  config = lib.mkIf cfg.enable ({
      cfg.xdg-autostart = lib.mkDefault true;
    }
    // (lib.mkIf cfg.xdg-autostart {
      xdg.autostart = {
        enable = lib.mkDefault true;
        entries = [
          "${flake.packages.${pkgs.stdenv.hostPlatform.system}.default}/share/applications/simple-wallpaper-engine.desktop"
        ];
      };
    }));
}
