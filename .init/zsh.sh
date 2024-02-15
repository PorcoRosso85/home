echo -e "\n"
echo "install zsh using nix"
nix profile install nixpkgs#zsh

echo -e "\n"
echo "you can choose make zsh as default shell or not"
echo "now make not as default shell"
# chsh -s $(which zsh)


echo -e "\n"
echo "install antigen"
curl -L git.io/antigen > ~/antigen.zsh
source ~/antigen.zsh

echo -e "\n"
echo "plugin by antigen"
echo "antigen bundle alpaca-honke/prowpt@main" >> ~/.zshrc
echo "antigen bundle zsh-users/zsh-autosuggestions" >> ~/.zshrc