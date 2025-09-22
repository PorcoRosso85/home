{
  description = "OpenCode HTTP Client - Minimal Core";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-darwin" "aarch64-linux" "x86_64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in {
      packages = forAllSystems (pkgs: {
        client-hello = pkgs.writeShellApplication {
          name = "opencode-client-hello";
          runtimeInputs = with pkgs; [ curl jq ];
          text = ''
            OPENCODE_URL="''${OPENCODE_URL:-http://127.0.0.1:4096}"
            MSG="''${1:-just say hi}"

            # Health check
            curl -fsS "$OPENCODE_URL/doc" >/dev/null || {
              echo "Server not reachable. Start: nix profile install nixpkgs#opencode; opencode serve --port 4096" >&2
              exit 1
            }

            # Create session and send message
            SID=$(curl -fsS -X POST "$OPENCODE_URL/session" -H 'Content-Type: application/json' -d '{}' | jq -r '.id')
            RESP=$(curl -fsS -X POST "$OPENCODE_URL/session/$SID/message" \
              -H 'Content-Type: application/json' \
              -d "$(jq -n --arg text "$MSG" '{ parts: [{ type: "text", text: $text }] }')")
            
            echo "$RESP" | jq -r '(.parts[]? | select(.type=="text") | .text) // .'
          '';
        };
      });

      apps = forAllSystems (pkgs: {
        client-hello = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.system}.client-hello}/bin/opencode-client-hello";
        };
      });
    };
}