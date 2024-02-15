# # Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# # Initialization code that may require console input (password prompts, [y/n]
# # confirmations, etc.) must go above this block; everything else may go below.
# if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
#   source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
# fi
# # To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
# [[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh


# source $HOME/.bash_profile

# common_profile() {
#   COMMON_PROFILE=$HOME/.common_profile
#   if [ -e $COMMON_PROFILE ]
#     then source $COMMON_PROFILE
#   fi
# }
# common_profile

source $HOME/antigen.zsh

antigen bundle alpaca-honke/prowpt@main
antigen bundle zsh-users/zsh-autosuggestions

antigen apply