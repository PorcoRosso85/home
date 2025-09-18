{ config, lib, pkgs, ... }:
{
  imports = [ ./hardware-configuration.nix ];
  
  # Boot loader
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  
  # Host identification
  networking.hostName = "nixos-vm";
  
  # System state version (DO NOT CHANGE)
  system.stateVersion = "25.05";
}