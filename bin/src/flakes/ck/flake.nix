{
  description = "ck - Semantic Grep by Embedding";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      
      perSystem = { config, self', inputs', pkgs, system, ... }:
        let
          overlays = [ (import inputs.rust-overlay) ];
          pkgs = import inputs.nixpkgs { inherit system overlays; };
          
          rustToolchain = pkgs.rust-bin.stable.latest.default.override {
            extensions = [ "rust-src" "rust-analyzer" ];
          };
          
          ck = pkgs.rustPlatform.buildRustPackage rec {
            pname = "ck-search";
            version = "0.4.5";

            src = pkgs.fetchFromGitHub {
              owner = "BeaconBay";
              repo = "ck";
              rev = version;
              hash = "sha256-SDJXLqlNUtS0ZUEwk4ZgRJg/ohFb4GcnZLGjUQNBF3g=";
            };

            cargoLock = {
              lockFile = "${src}/Cargo.lock";
            };

            nativeBuildInputs = with pkgs; [
              pkg-config
              rustToolchain
            ];

            buildInputs = with pkgs; [
              openssl
              onnxruntime
            ] ++ pkgs.lib.optionals pkgs.stdenv.isDarwin [
              pkgs.darwin.apple_sdk.frameworks.Security
              pkgs.darwin.apple_sdk.frameworks.SystemConfiguration
            ];

            # Disable network access during build
            __noChroot = false;
            
            # Set environment to use system ONNX Runtime instead of downloading
            ONNXRUNTIME_LIB_PATH = "${pkgs.onnxruntime}/lib";
            ORT_STRATEGY = "system";

            # Build the workspace
            cargoBuildFlags = [ "--bin" "ck" ];
            
            # Skip tests during build
            doCheck = false;

            meta = with pkgs.lib; {
              description = "Semantic grep by embedding - find code by meaning, not just keywords";
              homepage = "https://github.com/BeaconBay/ck";
              license = with licenses; [ asl20 mit ];
              mainProgram = "ck";
            };
          };
        in
        {
          packages = {
            default = ck;
            ck = ck;
          };

          devShells.default = pkgs.mkShell {
            inputsFrom = [ ck ];
            packages = with pkgs; [
              rustToolchain
              cargo-watch
              cargo-edit
            ];
          };
        };
    };
}