{ pkgs, ... }:

let
  fabric = pkgs.buildGoModule {
    name = "fabric";
    src = pkgs.fetchFromGitHub {
      owner = "danielmiessler";
      repo = "fabric";
      rev = "v1.4.51";
      sha256 = "";
    };
    vendorHash = "";
  };
in

with pkgs; [
  go
  # fabric # lsp-ai同様buildできず
]
