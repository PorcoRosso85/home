# https://stackoverflow.com/questions/52445961/how-do-i-fix-the-rust-error-linker-cc-not-found-for-debian-on-windows-10
apt install build-essential -y
# rustc --target=my_target_architecture -C linker=target_toolchain_linker my_rustfile.rs

git clone https://github.com/helix-editor/helix
cd helix
cargo install --path helix-term

ln -s $PWD/runtime ~/.config/helix/runtime
