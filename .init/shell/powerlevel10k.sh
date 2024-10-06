p10k_install() {
  app='powerlevel10k'
  rm -r /root/temp/$app
  git clone --depth=1 https://github.com/romkatv/powerlevel10k.git /root/temp/$app

  path=$( cd $(dirname $0); pwd)
  mv /root/temp/$app $path/
  echo 'source '$path'/'$app'/'$app'.zsh-theme' >> /root/.zshrc
  rm -r /root/temp/$app
}
p10k_install
