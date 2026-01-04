{ config, pkgs, ... }:

{
  # Nix configuration
  nix = {
    package = pkgs.nix;
    extraOptions = ''
      experimental-features = nix-command flakes
    '';
    settings.trusted-users = [ "nixos" ];
  };

  # Users configuration (no plaintext initial passwords)
  users.users.root = { };

  users.users.nixos = {
    isNormalUser = true;
    extraGroups = [
      "wheel"
      "networkmanager"
      "docker"
    ];
  };

  # System packages - minimal for recovery (rest in HM user layer)
  environment.systemPackages = with pkgs; [
    git
    fd
    ripgrep
    helix
    curl
    openssl
    tar
    gzip
    unzip
  ];

  # SSH configuration - security enhanced
  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "prohibit-password"; # key-based only for root
      PasswordAuthentication = false; # disable password auth entirely
    };
  };

  services.tailscale.enable = true;

  # Virtualization configuration
  # Docker virtualization (user requested)
  virtualisation.docker.enable = true;

  # Time zone and locale
  time.timeZone = "Asia/Tokyo";
  i18n.defaultLocale = "en_US.UTF-8";

  # Networking
  networking.networkmanager.enable = true;

}
