# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

common_profile() {
  COMMON_PROFILE=$HOME/.common_profile
  if [ -e $COMMON_PROFILE ]
    then source $COMMON_PROFILE
  fi
}
common_profile

source $HOME/antigen.zsh

source /nix/store/3dvpikignvs56d3njrhbimsafvfz064d-powerlevel10k-1.20.0/share/zsh-powerlevel10k/powerlevel10k.zsh-theme
