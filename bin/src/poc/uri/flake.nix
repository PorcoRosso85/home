{
  description = "LocationURI Dataset Management POC";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        python = pkgs.python312;
        
        # Python dependencies
        pythonDeps = with python.pkgs; [
          pytest
          pytest-cov
          pyyaml
          jinja2
        ];
        
        # ����Xpersistence/kuzu_py	
        kuzuPy = python.pkgs.buildPythonPackage {
          pname = "kuzu_py";
          version = "0.1.0";
          src = ../../persistence/kuzu_py;
          
          propagatedBuildInputs = with python.pkgs; [
            kuzu
          ];
          
          format = "pyproject";
          
          nativeBuildInputs = with python.pkgs; [
            setuptools
            wheel
          ];
        };
        
        # ,�ñ��
        uriPoc = python.pkgs.buildPythonPackage {
          pname = "uri-poc";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = [
            kuzuPy
          ] ++ pythonDeps;
          
          format = "pyproject";
          
          nativeBuildInputs = with python.pkgs; [
            setuptools
            wheel
          ];
        };
        
        # �z��
        devEnv = python.withPackages (ps: [
          kuzuPy
        ] ++ pythonDeps);
        
      in
      {
        packages.default = uriPoc;
        
        devShells.default = pkgs.mkShell {
          buildInputs = [
            devEnv
            pkgs.ruff
            pkgs.black
          ];
          
          shellHook = ''
            echo "LocationURI Dataset Management POC Development Environment"
            echo "Available commands:"
            echo "  nix run .             - Show available apps"
            echo "  nix run .#test        - Run tests"
            echo "  nix run .#cli         - Run interactive CLI"
            echo "  nix run .#demo        - Run demo scenario"
          '';
        };
        
        apps = rec {
          default = {
            type = "app";
            program = let
              appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
              helpText = ''
                ������: LocationURI Dataset Management POC
                
                ��:
                - requirement/graph ���ޒ(W_LocationURI�
                - persistence/kuzu_py k���������\
                - �M��U�_������K�n���\�1�
                
                )(��j����:
                ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
              '';
            in "${pkgs.writeShellScript "show-help" ''
              cat << 'EOF'
              ${helpText}
              EOF
            ''}";
          };
          
          test = {
            type = "app";
            program = "${pkgs.writeShellScript "test" ''
              cd ${self}
              export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
              exec ${devEnv}/bin/pytest test_mod.py -v
            ''}";
          };
          
          cli = {
            type = "app";
            program = "${pkgs.writeShellScript "cli" ''
              cd ${self}
              export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
              exec ${devEnv}/bin/python main.py
            ''}";
          };
          
          demo = {
            type = "app";
            program = "${pkgs.writeShellScript "demo" ''
              echo "LocationURI Dataset Management Demo"
              echo "==================================="
              echo ""
              echo "This demo will:"
              echo "1. Initialize an in-memory repository"
              echo "2. Show the allowed dataset"
              echo "3. Create some nodes from the dataset"
              echo "4. Try to create a node NOT in the dataset (will fail)"
              echo "5. List all created nodes"
              echo ""
              
              cd ${self}
              export PYTHONPATH="${self}:../../persistence/kuzu_py:$PYTHONPATH"
              
              ${devEnv}/bin/python << 'PYTHON_EOF'
import json
from mod import create_restricted_repository

# Initialize repository
print("Step 1: Initializing repository...")
repo = create_restricted_repository(":memory:")
print(" Repository initialized\n")

# Show allowed dataset
print("Step 2: Allowed dataset:")
dataset = repo["get_allowed_dataset"]()
print(f"Total allowed URIs: {dataset['count']}")
print("Sample URIs:")
for uri in dataset['uris'][:5]:
    print(f"  - {uri}")
print("...\n")

# Create some nodes
print("Step 3: Creating nodes from dataset:")
test_uris = ["req://system", "req://architecture", "req://security"]
for uri in test_uris:
    result = repo["create_locationuri_node"](uri)
    status = "" if result["type"] in ["Success", "AlreadyExists"] else ""
    print(f"  {status} {uri}: {result['type']}")
print()

# Try invalid node
print("Step 4: Attempting to create node NOT in dataset:")
invalid_uri = "req://custom/invalid/path"
result = repo["create_locationuri_node"](invalid_uri)
print(f"   {invalid_uri}: {result['type']} - {result['message']}\n")

# List nodes
print("Step 5: All nodes in database:")
nodes = repo["list_locationuris"]()
print(f"Total nodes: {nodes['count']}")
for uri in sorted(nodes['uris'])[:10]:
    print(f"  - {uri}")
if nodes['count'] > 10:
    print(f"  ... and {nodes['count'] - 10} more")

PYTHON_EOF
            ''}";
          };
          
          readme = {
            type = "app";
            program = "${pkgs.writeShellScript "show-readme" ''
              if [ -f ${self}/README.md ]; then
                cat ${self}/README.md
              else
                echo "README.md not found"
              fi
            ''}";
          };
        };
      }
    );
}