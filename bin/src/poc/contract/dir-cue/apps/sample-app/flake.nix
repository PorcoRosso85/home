{
  description = "Sample app for testing CUE contracts";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    governance-flake.url = "path:../..";
  };

  outputs = { self, nixpkgs, governance-flake }: {
    # Minimal sample app
    packages.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.hello;

    # Use governance-flake for validation
    checks.x86_64-linux.contracts = governance-flake.lib.x86_64-linux.cueContractCheck {
      src = ./.;
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    };
  };
}