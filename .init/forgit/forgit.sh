forgit() {
  path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
  echo $path
  if [ -d $path/bin ]; then
    rm -r $path/bin
    echo $path"/bin removed"
  fi
  git clone git@github.com:wfxr/forgit.git $path/bin
  rm -r $path/bin/.git
  echo "source "$path"/bin/forgit.plugin.sh" >> ~/.extension/bash/bashrc.sh
}

forgit
