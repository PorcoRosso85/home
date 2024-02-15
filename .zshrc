common_profile() {
  COMMON_PROFILE=$HOME/.common_profile
  if [ -e $COMMON_PROFILE ]
    then source $COMMON_PROFILE
  fi
}
common_profile

source $HOME/antigen.zsh

antigen bundle alpaca-honke/prowpt@main
antigen bundle zsh-users/zsh-autosuggestions

antigen apply