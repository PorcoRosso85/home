nvim_install() {
    extract="nvim-linux64.tar.gz"
    extracted="nvim-linux64"
    command="nvim"
    bin_path="/usr/bin"
    path=$( cd $(dirname $0); pwd)
    target_path="$HOME/.extension"

    echo $path "is the path of executed file"

    # Check if download is successful
    if ! wget -P $path "https://github.com/neovim/neovim/releases/download/stable/"$extract; then
        echo "Error: Failed to download $extract"
        exit 1
    fi

    # Check if extraction is successful
    if ! tar xzvf $path/$extract -C $path; then
        echo "Error: Failed to extract $extract"
        exit 1
    fi

    # Move extracted files to target directory
    if ! mv $path/$extracted $target_path; then
        echo "Error: Failed to move $extracted to $target_path"
        # Attempt to rollback by deleting extracted files
        rm -rf $path/$extracted
        exit 1
    fi

    # Make the command executable
    if ! chmod +x $target_path/$extracted/bin/$command; then
        echo "Error: Failed to make $command executable"
        # Attempt to rollback by moving extracted files back
        mv $target_path/$extracted $path
        exit 1
    fi

    # Check and remove if symbolic link or actual command already exists
    if [ -L $bin_path/$command ] || [ -f $bin_path/$command ]; then
        sudo rm $bin_path/$command
    fi

    # Create symbolic link
    sudo ln -s $target_path/$extracted/bin/$command $bin_path/$command

    # Check if symbolic link is created correctly
    if [ -L $bin_path/$command ] && [ "$(readlink $bin_path/$command)" = "$target_path/$extracted/bin/$command" ]; then
        echo "Symbolic link created successfully"
    else
        echo "Error: Symbolic link creation failed"
        # Attempt to rollback by moving extracted files back and removing broken link
        sudo rm $bin_path/$command
        mv $target_path/$extracted $path
        exit 1
    fi

    rm $path/$extract
}

nvim_install




# [plug]
vimplug() {
	echo "install vimplug"
	bash -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
	https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
}
vimplug

# nvim_win32yank() {
# 	path=$( cd $(dirname $0); pwd)
#   $path/nvim_win32yank.sh
# }



# git clone --depth 1 https://github.com/wbthomason/packer.nvim\
#   ~/.local/share/nvim/site/pack/packer/opt/packer.nvim

# for wsl2 to share clipboard
# git clone git@github.com:equalsraf/win32yank.git ~/.bashrcs/win32yank
# export PATH=$PATH:~/.bashrcs/
# this is one solution 'win32yank'
# another solution 'powershell' https://www.reddit.com/r/neovim/comments/g94zrl/solution_neovim_clipboard_with_wsl/
