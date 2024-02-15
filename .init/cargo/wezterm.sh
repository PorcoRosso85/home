#curl https://sh.rustup.rs -sSf | sh -s
curl -LO https://github.com/wez/wezterm/releases/download/20221119-145034-49b9839f/wezterm-20221119-145034-49b9839f-src.tar.gz
tar -xzf wezterm-20221119-145034-49b9839f-src.tar.gz
cd wezterm-20221119-145034-49b9839f
./get-deps
cargo build --release
cargo run --release --bin wezterm -- start
