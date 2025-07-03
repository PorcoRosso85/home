{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = {nixpkgs,...}: {
    packages = nixpkgs.lib.genAttrs ["x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin"] (s:
      let p=nixpkgs.legacyPackages.${s}; in {
        default = p.writeShellScriptBin "diff" ''
          PATH="${p.lib.makeBinPath[p.jq p.coreutils p.findutils]}:$PATH"
          exec ${p.bash}/bin/bash ${./diff.sh} "$@"
        '';
      });
  };
}