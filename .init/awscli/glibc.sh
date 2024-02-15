glibc_install() {
  cd /root/temp
  git clone https://sourceware.org/git/glibc.git
  cd glibc
  git checkout release/2.36/master
}
# glibc_install
# https://qiita.com/miyase256/items/e7e0ea017189c13fd50f
