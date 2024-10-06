# https://yannmjl.medium.com/how-to-manually-update-curl-on-ubuntu-server-899476062ad6, https://yannmjl.medium.com/how-to-manually-update-curl-on-ubuntu-server-899476062ad6
curl_install {
  version="7.86.0"
  apt remove curl -y
  apt purge curl
  apt-get update
  apt-get install -y libssl-dev autoconf libtool make

  cd /usr/local/src
  rm -rf curl*
  wget "https://curl.haxx.se/download/curl-"$version".zip"
  unzip "curl-"$version".zip"

  cd "curl-"$version     # enter the directory where curl was unpacked #
  ./buildconf
  ./configure --with-ssl 
  make
  make install

  mv /usr/bin/curl /usr/bin/curl.bak
  cp /usr/local/bin/curl /usr/bin/curl

  ldconfig
}
curl_install
