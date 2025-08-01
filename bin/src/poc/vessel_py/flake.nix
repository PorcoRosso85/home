{
  description = "Vessel - Dynamic script execution container system";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # �,�j�X��
          pytest
          requests
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            # Bun for TypeScript vessels
            bun
          ];
          
          shellHook = ''
            echo "Vessel Development Environment"
            echo "Python: $(python --version)"
            echo "Bun: $(bun --version)"
          '';
        };
        
        packages = {
          test = pkgs.writeShellScriptBin "test" ''
            echo "Running Python vessel tests..."
            ${pythonEnv}/bin/pytest -v
          '';
        };
        
        apps = {
          test = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "test" ''
              cd /home/nixos/bin/src/poc/vessel_py
              export PATH="${pythonEnv}/bin:$PATH"
              ${pythonEnv}/bin/python test_pipeline.py
            ''}/bin/test";
          };
          
          vessel = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "vessel" ''
              cd /home/nixos/bin/src/poc/vessel_py
              ${pythonEnv}/bin/python vessel.py "$@"
            ''}/bin/vessel";
          };
        };
      }
    );
}