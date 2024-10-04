home-managerは事前にuserの作成が必要
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
