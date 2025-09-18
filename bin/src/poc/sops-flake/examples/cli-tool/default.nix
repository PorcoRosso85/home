{ pkgs ? import <nixpkgs> {} }:

pkgs.stdenv.mkDerivation rec {
  pname = "sops-cli-tool";
  version = "1.0.0";
  
  src = ./.;
  
  buildInputs = with pkgs; [
    bash
    sops
    age
    jq
    yq
  ];
  
  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/share/secrets
    
    # Install the main script
    cat > $out/bin/sops-cli-tool <<'EOF'
    #!/usr/bin/env bash
    exec ${pkgs.bash}/bin/bash ${./cli-tool.sh} "$@"
    EOF
    chmod +x $out/bin/sops-cli-tool
    
    # Copy configuration if exists
    if [[ -d ./secrets ]]; then
      cp -r ./secrets $out/share/
    fi
  '';
  
  meta = with pkgs.lib; {
    description = "CLI tool with SOPS-managed configuration";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}