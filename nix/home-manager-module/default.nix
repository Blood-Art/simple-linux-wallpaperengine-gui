flake: {
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.services.simple-wallpaper-engine;
in {
  options.services.simple-wallpaper-engine = {
    enable = lib.mkEnableOption "Wallpaper service (user systemd)";

    # Optional: make it wait for your compositor / session bits.
    after = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = ["graphical-session.target"];
      description = "systemd units to start after.";
    };

    wants = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = ["graphical-session.target"];
      description = "systemd units to pull in.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.user.services.simpl-wallpaper-engine = {
      Unit = {
        Description = "Set wallpaper";
        After = cfg.after;
        Wants = cfg.wants;
        PartOf = ["graphical-session.target"];
      };

      Service = {
        Type = "simple";
        ExecStart = "${lib.getExe flake.packages.${pkgs.system}.default} --background";

        Restart = "always";
        RestartSec = 10;

        Environment = [
          "XDG_RUNTIME_DIR=%t"
        ];
      };

      Install = {
        WantedBy = ["graphical-session.target"];
      };
    };
  };
}
