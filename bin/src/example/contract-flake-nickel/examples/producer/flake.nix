{
  description = "Example producer implementing Nickel contract";

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
      packages.${system}.default = pkgs.writeShellScriptBin "producer" ''
        ${pkgs.nickel}/bin/nickel eval -f json << 'EOF'
        let contracts = import "${contract-flake}/contracts.ncl" in
        {
          processed = 42,
          failed = 3,
          output = ["task-001", "task-002", "task-003"],
        } & contracts.ProducerContract
        EOF
      '';
    };
}