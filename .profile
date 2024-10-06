# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi


# [alias]
#alias cdf='cd $(find . -maxdepth 3 -type d | fzf)'
alias cdfm='cd $(find /mnt/c/Users/admin.DESKTOP-1PF4AT3/ -maxdepth 3 -type d | grep "Documents\|Downloads\|wsl" | fzf)'
alias catf='cat $(find . -maxdepth 4 | fzf)'


# [alias/docker]
alias dcir='docker image rm'
alias dccl='docker container ls -a'
alias dccr='docker container rm'
alias dcsp='docker system purge'
alias dce='docker exec'


eval "$(direnv hook bash)"

export LD_LIBRARY_PATH=/nix/store/g3g89nki211vi892cr6vg57aihvjk302-z3-4.8.15-python/lib/python3.10/site-packages/z3/lib/libz3.so:/nix/store/rgdmlsv1fn32pwclapv6zi59fyjc3zf2-z3-4.8.15-lib/lib/libz3.so

# Set PATH, MANPATH, etc., for Homebrew.
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
