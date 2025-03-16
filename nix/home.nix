{ config, pkgs, lib, ... }:

let
  # username = builtins.getEnv "USER";
  # username = "nixos";
in
{
  programs = {
    home-manager.enable = true;

    bash = {
      enable = true;
        initExtra = ''
          export TERM="xterm-256color"
          export COLORTERM="truecolor"
          eval "$(dircolors -b)"
          source "$HOME/.cargo/env" # 必要に応じて
        # - Bash インタラクティブ シェルの初期化
        # - 別名 (alias)、関数、環境変数の設定
        # - シェルの動作をカスタマイズする設定
        # このファイルは新しいシェルが起動するたびに読み込まれます
        # ==================================================
        source $HOME/_.bashrc
        # source $HOME/todo.sh

        # If not running interactively, don't do anything
        case $- in
            *i*) ;;
              *) return;;
        esac

        # don't put duplicate lines or lines starting with space in the history.
        # See bash(1) for more options
        HISTCONTROL=ignoreboth

        # append to the history file, don't overwrite it
        shopt -s histappend

        # for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
        # HISTSIZE=1000
        HISTFILESIZE=2000

        # check the window size after each command and, if necessary,
        # update the values of LINES and COLUMNS.
        shopt -s checkwinsize

        # make less more friendly for non-text input files, see lesspipe(1)
        [ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

        # set variable identifying the chroot you work in (used in the prompt below)
        if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
            debian_chroot=$(cat /etc/debian_chroot)
        fi

        # set a fancy prompt (non-color, unless we know we "want" color)
        case "$TERM" in
            xterm-color|*-256color) color_prompt=yes;;
        esac

        if [ -n "$force_color_prompt" ]; then
            if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
                # We have color support; assume it's compliant with Ecma-48
                # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
                # a case would tend to support setf rather than setaf.)
                color_prompt=yes
            else
                color_prompt=
            fi
        fi

        if [ "$color_prompt" = yes ]; then
            PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
        else
            PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
        fi
        unset color_prompt force_color_prompt

        # If this is an xterm set the title to user@host:dir
        case "$TERM" in
        xterm*|rxvt*)
            PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
            ;;
        *)
            ;;
        esac

        # enable color support of ls and also add handy aliases
        if [ -x /usr/bin/dircolors ]; then
            test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
            alias ls='ls --color=auto'
            #alias dir='dir --color=auto'
            #alias vdir='vdir --color=auto'

            alias grep='grep --color=auto'
            alias fgrep='fgrep --color=auto'
            alias egrep='egrep --color=auto'
        fi

        # some more ls aliases
        alias ll='ls -alF'
        alias la='ls -A'
        alias l='ls -CF'

        # Add an "alert" alias for long running commands.  Use like so:
        #   sleep 10; alert
        alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

        # Alias definitions.
        # You may want to put all your additions into a separate file like
        # ~/.bash_aliases, instead of adding them here directly.
        # See /usr/share/doc/bash-doc/examples in the bash-doc package.

        # TODO: 別ファイルへ移行 $HOME/.config/shell/bash_aliases に移動して、このファイルからは削除
        if [ -f ~/.bash_aliases ]; then
            . ~/.config/shell/bash_aliases
        fi

        # enable programmable completion features (you don't need to enable
        # this, if it's already enabled in /etc/bash.bashrc and /etc/profile
        # sources /etc/bash.bashrc).
        if ! shopt -oq posix; then
          if [ -f /usr/share/bash-completion/bash_completion ]; then
            . /usr/share/bash-completion/bash_completion
          elif [ -f /etc/bash_completion ]; then
            . /etc/bash_completion
          fi
        fi

        # eval "$(starship init bash)"

        for file in $HOME/.config/shell/*.sh; do
            source "$file"
            # echo "sourced $file"
        done

        # export GO111MODULE=on

        # export GOPATH=
        export EDITOR=hx
        '';
        shellAliases = {
          ll = "ls -alF";
          la = "ls -A";
          l = "ls -CF";
          # その他のエイリアス
        };
    };

    # dircolors = { enable = true; }; # カスタムカラーが必要ならここで設定

    starship = {
      enable = true;
      # settings = { ... }; # starship の設定が必要ならここで追加
    };

    tmux = {
        enable = true;
    };

    direnv = {
      enable = true;
      enableBashIntegration = true; # see note on other shells below
      nix-direnv.enable = true;
    };

  };

  home.packages = with pkgs; [
    unzip
    tre-command
    fzf
    ripgrep
    fd
    bat
    zoxide
    eza
    broot

    # aider-chat
  ] ++ (import ./language.nix { inherit pkgs; });

  home.file.".profile".text = ''
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


    # Set PATH, MANPATH, etc., for Homebrew.
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    #!/bin/bash

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

    alias ls='ls --color=auto -la'


    glp() {
      preview="git diff $@ --color=always -- {-1}"
      git diff $@ --name-only | fzf -m --ansi --preview $preview
    }

    mkcd() {
      if ! [ -d $1 ]; then
        mkdir $1
        echo "made dir" $1
      fi
      cd $1
    }


    # [Fzf]
    export FZF_DEFAULT_COMMAND="fd" #"find . -printf '%Tm/%Td %TH:%TM %p\n'"
    export FZF_DEFAULT_OPTS="--layout=reverse --height 40%"
    FZF_CTRL_T_COMMAND="find . -maxdepth 4"
    FZF_CTRL_R_OPTS="--reverse --height 25%"

    fz() {
      local sels=( "${(@f)$(fd --color=always . "${@:2}" | fzf -m --height=25% --reverse --ansi)}" )
      [ -n "$sels" ] && print -z -- "$1 ${sels[@]:q:q}"
    }

    cmdf() {
      local command_file_path="$HOME/.extension/shell/commands.sh"
      local sels=( "${(@f)$(cat $command_file_path | fzf -m --height=25% --reverse --ansi)}" )
      [ -n "$sels" ] && print -z -- "$1 ${sels[@]}"
    }

    cmda() {
      local command_file_path="$HOME/.extension/shell/commands.sh"
      echo $1 >> $command_file_path
    }

    cmdc() {
      local command_file_path="$HOME/.extension/shell/commands.sh"
      nvim $command_file_path
    }


    ff() { 
      fd $1 $2 | fzf --preview 'bat --style=numbers --color=always --line-range :500 {}'
    }

    fw() {
      fd $1 -t f $2 | xargs grep -n -E -w "$3" | fzf
    }

    jq_() {
      case $1 in
        "jc")
          shift # $1を削除して、$2が$1に、$3が$2に、...
          jq_jc "$@"
          ;;
        "jm")
          shift
          jq_jm "$@"
          ;;
        "cj")
          shift
          jq_cj "$@"
          ;;
        *)
          echo "Invalid argument. Use 'jc', 'jm', or 'cj'."
          ;;
      esac
    }

    jq_jc() {
      jq -r '.stock[] | [.id, .item, .description] | @csv' $1
    }

    jq_jm() {
      jq -r '. | sort_by((.location.path | explode | map(-.)), .location.lines.begin) | .[] | @text "| [\(.location.path):\(.location.lines.begin)](../blob/BRANCH-NAME/\(.location.path)#L\(.location.lines.begin)) | \(.description)"' gl-code-quality-report.json
    }

    jq_cj() {
      jq -R -s -f $1 $2 |jq 'del(.[][] | nulls)' |head -n -2 | sed -e 1d -e 's/},/}/g' | jq . -c | sed "s/^/{ \"index\" :{} }\n/g" > $3
    }

    gloj() {
      # https://scrapbox.io/nwtgck/git%E6%A8%99%E6%BA%96%E3%81%A0%E3%81%91%E3%81%A7%E3%80%81log%E3%81%AE%E6%83%85%E5%A0%B1%E3%82%92JSON%E3%81%AB%E3%81%97%E3%81%A6%E5%8F%96%E5%BE%97%E3%81%99%E3%82%8B%E6%96%B9%E6%B3%95
      git log --pretty=format:'{%n  "commit": "%H",%n  "abbreviated_commit": "%h",%n  "tree": "%T",%n  "abbreviated_tree": "%t",%n  "parent": "%P",%n  "abbreviated_parent": "%p",%n  "refs": "%D",%n  "encoding": "%e",%n  "subject": "%s",%n  "sanitized_subject_line": "%f",%n  "body": "%b",%n  "commit_notes": "%N",%n  "verification_flag": "%G?",%n  "signer": "%GS",%n  "signer_key": "%GK",%n  "author": {%n    "name": "%aN",%n    "email": "%aE",%n    "date": "%aD"%n  },%n  "commiter": {%n    "name": "%cN",%n    "email": "%cE",%n    "date": "%cD"%n  }%n},'
      # https://gist.github.com/varemenos/e95c2e098e657c7688fd
    }


    export LD_LIBRARY_PATH=/nix/store/g3g89nki211vi892cr6vg57aihvjk302-z3-4.8.15-python/lib/python3.10/site-packages/z3/lib/libz3.so:/nix/store/rgdmlsv1fn32pwclapv6zi59fyjc3zf2-z3-4.8.15-lib/lib/libz3.so

    # bindkey -v
    # bind -vi '"\e[1;9D": backward-word'
    # bind -vi '"\e[1;9C": forward-word'
    # bindkey -a '^[[1;9D' backward-word
    # bindkey -a '^[[1;9C' forward-word
    # bindkey -v -a '^C' vi-cmd-mode

    # bind '"\C-n": history-search-forward'
    # bind '"\C-p": history-search-backward'
    # HISTSIZE=100000

    export EDITOR=hx
  '';
}