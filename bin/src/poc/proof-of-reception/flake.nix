{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-readme.url = "path:../flake-readme";
  };

  outputs = inputs@{ flake-parts, flake-readme, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ flake-readme.flakeModules.readme ];
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      perSystem = {
        readme = {
          enable = true;
          ignoreExtra = [
            "contracts"
            "verticals/sales-bd"
            # サブ機能ディレクトリを作るまでは除外のまま
            "platform/event-header"
            "platform/durable-log"
            "platform/audit-trail"
            "verticals/compliance-legal/monitor"
            "verticals/compliance-legal/tracker"
          ];
        };
      };
    };
}