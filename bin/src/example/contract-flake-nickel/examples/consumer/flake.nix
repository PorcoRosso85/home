{
  description = "Example consumer implementing Nickel contract";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    contract-flake.url = "path:../..";
  };

  outputs = { self, nixpkgs, contract-flake }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.default = pkgs.writeShellScriptBin "consumer" ''
        input=$(cat)
        ${pkgs.nickel}/bin/nickel eval -f json << EOF
        let contracts = import "${contract-flake}/contracts.ncl" in
        {
          summary = "Consumed data successfully",
          details = $input,
        } & contracts.ConsumerContract
        EOF
      '';
    };
}