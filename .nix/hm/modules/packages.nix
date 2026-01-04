{ pkgs, ... }:

{
  home.packages = with pkgs; [
    # UX packages (daily + weekly)
    gh
    fzf
    starship
    bat
    delta
    zoxide
    yazi
    lazygit
    wezterm
    jq
    yq

    # Nix LSP/formatter
    nixd
    nixfmt-rfc-style

    # CLI補助
    nh
    shellcheck
    shfmt
  ];
}
