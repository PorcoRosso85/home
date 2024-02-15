awscli_install() {
	#extract="nvim-linux64.tar.gz"
	#extracted="nvim-linux64"
	#command="nvim"
	##path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
	path=$( cd $(dirname $0); pwd)
	#echo $path "is the path of executed file"

	#if [ -f $path/$extract ]; then
	#	rm -r $path/$extract
	#	echo $path/$extract" removed"
	#fi

  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o $path/"awscliv2.zip"
  unzip $path/awscliv2.zip
  $path/aws/install

	#if [ -f /usr/bin/$command ]; then
	#	rm /usr/bin/$command
	#	echo "/usr/bin/"$command" removed"
	#fi

	#ln -s $path/$extracted/bin/$command /usr/bin/$command
}
awscli_install
