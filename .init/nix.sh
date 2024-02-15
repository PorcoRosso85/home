echo "init nix"
init_nix() {
    sudo systemctl stop nix-daemon.service
    sudo systemctl disable nix-daemon.socket nix-daemon.service
    sudo systemctl daemon-reload

    items_deleted=(
        "/etc/bashrc"
        "/etc/bashrc.backup-before-nix"
        "/etc/profile.d/nix.sh"
        "/etc/profile.d/nix.sh.backup-before-nix"
        "/etc/profile.d/nix.sh.backup-before-nix"
        "/etc/zshrc"
        "/etc/zshrc.backup-before-nix"
        "/etc/bash.bashrc"
        "/etc/bash.bashrc.backup-before-nix"
        "/etc/nix"
        "/nix"
        "/var/root/.nix-profile"
        "/var/root/.nix-defexpr"
        "/var/root/.nix-channels"
        "/Users/simonbein/.nix-profile"
        "/Users/simonbein/.nix-defexpr"
        "/Users/simonbein/.nix-channels"
    )

    for item in "${items_deleted[@]}"; do
        sudo rm -rf "$item"
    done

    for i in $(seq 1 32); do
      sudo userdel nixbld$
    done
    sudo groupdel nixbld

}
init_nix

bash <(curl -L https://nixos.org/nix/install) --daemon
