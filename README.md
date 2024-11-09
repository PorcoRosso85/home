# home for user `<branch name>`

## description

### create user on nixos(with wsl)

`/etc/nixos/configuration.nix`

```nix
{ config, lib, pkgs, ... }:

{
  imports = [
    # include NixOS-WSL modules
    <nixos-wsl/modules>
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";

  system.stateVersion = "24.05";

  users.users.roccho = {
    isNormalUser = true;
    password = ""; # set password up here
    extraGroups = [ "wheels" ];
  };

  nix = {
    package = pkgs.nix;
    extraOptions = ''
      experimental-features = nix-command flakes
    '';
  };
}
```

### this file is for

1. configure the home with nix
   1. nix, home-manager
   2. git


### requirements before `nix build` and apply built home-manager configuration

<details>
<summary>without clone</summary>

* `nix build github:PorcoRosso85/home/branch_name#homeConfigurations.roccho.activationPackage`

<details>
<summary>with clone</summary>

* `git init`
* `git remote add origin https://github.com/PorcoRosso85/home.git`
* checkout to branch 'branch_name'
* `nix build .#homeConfigurations.roccho.activationPackage`
* `./result/activate`
