nvim_install() {
	extract="nvim-linux64.tar.gz"
	extracted="nvim-linux64"
	command="nvim"
	#path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
	path=$( cd $(dirname $0); pwd)
	echo $path "is the path of executed file"

	if [ -f $path/$extract ]; then
		rm -r $path/$extract
		echo $path/$extract" removed"
	fi

	wget -P $path "https://github.com/neovim/neovim/releases/download/stable/"$extract
	tar xzvf $path/$extract -C $path
	chmod +x $path/$extracted/bin/$command

	if [ -f /usr/bin/$command ]; then
		rm /usr/bin/$command
		echo "/usr/bin/"$command" removed"
	fi

	ln -s $path/$extracted/bin/$command /usr/bin/$command

  cp $path/nvim_paste /root/.config/nvim/nvim_paste
}
nvim_install

# [plug]
vimplug() {
  sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
       https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
}
vimplug

nvim_win32yank() {
	path=$( cd $(dirname $0); pwd)
  $path/nvim_win32yank.sh
}



# git clone --depth 1 https://github.com/wbthomason/packer.nvim\
#   ~/.local/share/nvim/site/pack/packer/opt/packer.nvim

# for wsl2 to share clipboard
# git clone git@github.com:equalsraf/win32yank.git ~/.bashrcs/win32yank
# export PATH=$PATH:~/.bashrcs/
# this is one solution 'win32yank'
# another solution 'powershell' https://www.reddit.com/r/neovim/comments/g94zrl/solution_neovim_clipboard_with_wsl/
