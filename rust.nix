{ pkgs, ... }:

let
  lsp-ai = pkgs.rustPlatform.buildRustPackage {
    pname = "lsp-ai";
    version = "0.7.1";
    src = pkgs.fetchFromGitHub {
      owner = "SilasMarvin";
      repo = "lsp-ai";
      rev = "7cf9477c8393fe2bc74c0f78871b0c94fe70cedb";
      sha256 = ""; # おそらく空白でOK
    };
    cargoSha256 = ""; 
    # # Golang environment variables
    # export GOROOT=/usr/local/go
    # export GOPATH=$HOME/go

    # # Update PATH to include GOPATH and GOROOT binaries
    # export PATH=$GOPATH/bin:$GOROOT/bin:$HOME/.local/bin:$PATH
  };
in
with pkgs; [
  rustup
  # lsp-ai
]
