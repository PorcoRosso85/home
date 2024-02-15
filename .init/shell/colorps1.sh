if [ "$color_prompt" = yes ]; then
    # Default color prompt:
    #PS1='$${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
 
    # Read Mike's custom prompt, apply it to PS1.
    source "$HOME/.mkps1.sh"
    PS1="$(__mkps1)"
else
    # Modified to support git status in PS1.
    # Also modified by Mike to function better.
    #PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
    PS1='\n${debian_chroot:+($debian_chroot)}\u:\w$(__git_ps1 " (%s)")\n\$ '
fi

## https://unix.stackexchange.com/questions/148/colorizing-your-terminal-and-shell-environment
#export TERM=xterm-color
#export GREP_OPTIONS='--color=auto' GREP_COLOR='1;32'
#export CLICOLOR=1
#export LSCOLORS=ExFxCxDxBxegedabagacad
#export COLOR_NC='\e[0m' # No Color
#export COLOR_BLACK='\e[0;30m'
#export COLOR_GRAY='\e[1;30m'
#export COLOR_RED='\e[0;31m'
#export COLOR_LIGHT_RED='\e[1;31m'
#export COLOR_GREEN='\e[0;32m'
#export COLOR_LIGHT_GREEN='\e[1;32m'
#export COLOR_BROWN='\e[0;33m'
#export COLOR_YELLOW='\e[1;33m'
#export COLOR_BLUE='\e[0;34m'
#export COLOR_LIGHT_BLUE='\e[1;34m'
#export COLOR_PURPLE='\e[0;35m'
#export COLOR_LIGHT_PURPLE='\e[1;35m'
#export COLOR_CYAN='\e[0;36m'
#export COLOR_LIGHT_CYAN='\e[1;36m'
#export COLOR_LIGHT_GRAY='\e[0;37m'
#export COLOR_WHITE='\e[1;37m'
#case $TERM in
#     xterm*|rxvt*)
#         local TITLEBAR='\[\033]0;\u ${NEW_PWD}\007\]'
#          ;;
#     *)
#         local TITLEBAR=""
#          ;;
#    esac
#
#local UC=$COLOR_WHITE               # user's color
#[ $UID -eq "0" ] && UC=$COLOR_PURPLE   # root's color
#
#PS1="$TITLEBAR\n\[${UC}\]\u \[${COLOR_LIGHT_BLUE}\]\${PWD} \n\[${COLOR_LIGHT_GREEN}\]→\[${COLOR_NC}\] "
