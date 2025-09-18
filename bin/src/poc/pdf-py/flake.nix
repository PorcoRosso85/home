{
  description = "PDF text extraction with OCR - minimal dependencies";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          # Essential dependencies only
          pymupdf      # PDF processing
          pytesseract  # OCR Python wrapper
          pillow       # Image processing for OCR
          requests     # HTTP downloads
          psutil       # Process and system monitoring
          # Testing dependencies
          pytest       # Testing framework
          matplotlib   # Visualization for layer mapping
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            tesseract  # OCR engine (system package)
          ];
          
          shellHook = ''
            echo "PDF Text Layer Detection POC"
            echo "============================"
            echo "Python packages: pymupdf, pytesseract, pillow, pytest, matplotlib"
            echo "System packages: tesseract"
            echo ""
            echo "Usage:"
            echo "  python -m pytest test_text_layer_detection.py -v  # Run tests"
            echo "  python text_layer_detector.py                     # Demo"
          '';
        };

        packages.default = pkgs.writeScriptBin "pdf-extract" ''
          #!${pkgs.bash}/bin/bash
          ${pythonEnv}/bin/python pdf_extractor.py "$@"
        '';
      });
}