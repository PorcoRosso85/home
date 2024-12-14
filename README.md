# home for `<branchName> user`

## 

### create user on nixos / wsl2

`/etc/nixos/configuration.nix`

```nix
{ config, lib, pkgs, ... }:

{
  imports = [
    <nixos-wsl/modules>
    /etc/nixos/modules/vscode.nix
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";
  # vscode-remote-workaround.enable = true;

  system.stateVersion = "24.05";

  environment.systemPackages = [
    pkgs.wget
    pkgs.helix
  ];

  security.sudo.enable = true;
  security.sudo.extraRules = [
    {
      groups = [ "wheel" ];  # wheel グループを対象に
      commands = [
        {
          command = "ALL";  # すべてのコマンドを許可
          options = [ "SETENV" "NOPASSWD" ];  # パスワードなしで実行可能
        }
      ];
    }
  ];

  programs.nix-ld = {
    enable = true;
    package = pkgs.nix-ld-rs; # only for NixOS 24.05
  };

  users.users.roccho = {
    isNormalUser = true;
    password = "roccho"; # set password up here
    # password = "$6$mKwV.T7nIO3yqW8k$3TWXPmb5zBMKK3.Uk3K1LEq40eOdh1RBQ0qBymmMzNAhjWxeaBbi3nN17lA/T5j/7kG8214xHFX3B/7bguzMn.";
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

and then, in terminal...

`sudo nixos-rebuild switch`


### requirements before `nix build` and apply built home-manager configuration

<details>
<summary>without clone</summary>

* `nix build github:PorcoRosso85/home/<branchName>#homeConfigurations.roccho.activationPackage`
</details>

<details>
<summary>with clone</summary>

* `git init`
* `git remote add origin https://github.com/PorcoRosso85/home.git`
* checkout to branch 'branch_name'
* `nix build .#homeConfigurations.roccho.activationPackage`
* `./result/activate`
</details>
