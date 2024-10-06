# dots
This is the place where
* initialize new os with shell and dot files
* my dotfiles is
* how dotfiles to be update
* how updated dotfiles to be restore to new terminal

## dots
curl -sS -o /tmp/dots.sh https://raw.githubusercontent.com/PorcoRosso85/dots/main/.init/dots.sh && bash /tmp/dots.sh && rm /tmp/dots.sh

## nix
bash $HOME/.init/nix.sh

## init
bash $HOME/.init/init.sh
home-managerは事前にuserの作成が必要

##

### note

```
user@g6i3:~$ sudo useradd -m -s /bin/bash roccho
[sudo] password for user: 
user@g6i3:~$ sudo -u roccho mkdir -p /home/roccho
user@g6i3:~$ sudo passwd roccho
New password: 
Retype new password: 
passwd: password updated successfully
user@g6i3:~$ sudo adduser roccho
adduser: The user `roccho' already exists.
user@g6i3:~$ sudo usermod -aG sudo roccho
user@g6i3:~$ groups roccho
roccho : roccho sudo
user@g6i3:~$ su - roccho
```
