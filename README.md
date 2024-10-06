# home for user `roccho`

## description

### this file is for

1. configure the home with nix
   1. nix, home-manager
   2. git
2.

### requirements before `nix build` and apply built home-manager configuration

* requires manually
  * create `roccho` user
  * add `roccho` to `sudo` group
  * set password for `roccho`
  * `sudo` privileges

```
$ sudo useradd -m -s /bin/bash roccho
[sudo] password for user: 
$ sudo -u roccho mkdir -p /home/roccho
$ sudo passwd roccho
New password: 
Retype new password: 
passwd: password updated successfully
$ sudo adduser roccho
adduser: The user `roccho' already exists.
$ sudo usermod -aG sudo roccho
$ groups roccho
roccho : roccho sudo

# check
$ su - roccho
```

### after clone

* `nix build`
  * `nix run .#homeConfigurations.roccho.activationPackage`
* `./result/activate`

```
# terminal

$ nix build .#homeConfigurations.rocchoHome.activationPackage
$ ./result/activate
```
