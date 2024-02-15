curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup component add rust-src
export PATH=$PATH:/root/.rustup/toolchains/nightly-x86_64-unkown-linux-gnu/bin

source ~/.cargo/env
echo "done source ~/.cargo/env"
