nvim_win32yank() {
	#extract="nvim-linux64.tar.gz"
	#extracted="nvim-linux64"
	#command="nvim"
	#path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
	path=$( cd $(dirname $0); pwd)
	echo $path "is the path of executed file"

	#if [ -f $path/$extract ]; then
	#	rm -r $path/$extract
	#	echo $path/$extract" removed"
	#fi

  wget -P $path/tmp/win32yank.zip "https://github.com/equalsraf/win32yank/releases/download/v0.0.4/win32yank-x64.zip"
  unzip -p $path/tmp/win32yank.zip win32yank.exe > $path/tmp/win32yank.exe
  chmod +x $path/tmp/win32yank.exe
  mv $path/tmp/win32yank.exe /usr/local/bin/

	#if [ -f /usr/bin/$command ]; then
	#	rm /usr/bin/$command
	#	echo "/usr/bin/"$command" removed"
	#fi

	#ln -s /tmp/win32yank.exe /usr/local/bin/
}
nvim_win32yank

