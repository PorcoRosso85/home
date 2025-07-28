# 他のFlakeからの使用例

## 1. Pythonパッケージとして使用

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    asvs-ref.url = "path:/home/nixos/bin/src/poc/asvs_reference";
  };

  outputs = { self, nixpkgs, asvs-ref }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      
      # ASVSパッケージを取得
      asvsConverter = asvs-ref.packages.${system}.default;
      
      # またはlibから取得
      asvsConverterLib = asvs-ref.lib.asvsArrowConverter;
      
      # ASVS 5.0データ
      asvs5Data = asvs-ref.lib.asvs5Data;
      
      pythonEnv = pkgs.python312.withPackages (ps: [
        asvsConverter
        ps.pandas  # 分析用
      ]);
    in
    {
      packages.default = pkgs.writeShellScriptBin "analyze-asvs" ''
        ${pythonEnv}/bin/python << 'EOF'
        from asvs_arrow_converter import ASVSArrowConverter
        import pyarrow.parquet as pq
        
        # Nixが提供するASVS 5.0データを使用
        converter = ASVSArrowConverter("${asvs5Data}/en")
        table = converter.get_requirements_table()
        
        print(f"Total requirements: {table.num_rows}")
        
        # Parquetとして保存
        pq.write_table(table, "asvs_analysis.parquet")
        EOF
      '';
    };
}
```

## 2. コンバーターを直接使用

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    asvs-ref.url = "path:/home/nixos/bin/src/poc/asvs_reference";
  };

  outputs = { self, nixpkgs, asvs-ref }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.default = pkgs.writeShellScriptBin "convert-asvs" ''
        # ASVSデータは自動的にGitHubから取得される
        ${asvs-ref.apps.${system}.convert-example.program}
      '';
    };
}
```

## 3. 開発環境での統合

```nix
{
  devShells.default = pkgs.mkShell {
    buildInputs = [
      # ASVS変換ツールを開発環境に含める
      (pkgs.python312.withPackages (ps: [
        asvs-ref.packages.${system}.default
        ps.jupyter
        ps.pandas
        ps.duckdb
      ]))
    ];
    
    shellHook = ''
      echo "ASVS Arrow Converter available"
      echo "Run: python -c 'from asvs_arrow_converter import ASVSArrowConverter'"
    '';
  };
}
```

## 利用可能なエクスポート

- `packages.default`: ASVSArrowConverter Pythonパッケージ
- `packages.python-env`: パッケージを含むPython環境
- `lib.asvsArrowConverter`: Pythonパッケージ（直接参照用）
- `lib.asvs5Data`: GitHub由来のASVS 5.0データ
- `apps.arrow-cli`: CLIツール
- `apps.convert-example`: 変換サンプル実行