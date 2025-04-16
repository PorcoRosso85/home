COZO_VERSION=0.7.5

COZO_PLATFORM=x86_64-unknown-linux-gnu # for Linux
#COZO_PLATFORM=aarch64-apple-darwin # uncomment for ARM Mac
#COZO_PLATFORM=x86_64-apple-darwin # uncomment  for Intel Mac
#COZO_PLATFORM=x86_64-pc-windows-gnu # uncomment for Windows PC

URL=https://github.com/cozodb/cozo/releases/download/v${COZO_VERSION}/libcozo_c-${COZO_VERSION}-${COZO_PLATFORM}.a.gz

mkdir libs
echo "Download from ${URL}"
curl -L $URL -o libs/libcozo_c.a.gz
gunzip -f libs/libcozo_c.a.gz
export CGO_LDFLAGS="-L/${PWD}/libs"
