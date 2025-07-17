# Persistence Layer with KuzuDB

NixでカスタマイズされたKuzuDBを提供するパッケージです。

## 使い方

### 1. カスタマイズされたkuzuのみを使用

```nix
{
  inputs.persistence.url = "path:/path/to/persistence";
  
  outputs = { self, nixpkgs, persistence }: {
    # カスタムkuzuパッケージを使用
    devShells.default = pkgs.mkShell {
      buildInputs = [
        persistence.packages.${system}.kuzu
      ];
    };
  };
}
```

### 2. persistence モジュール付きPython環境

```nix
{
  # persistence モジュールとkuzuが含まれたPython環境
  devShells.default = pkgs.mkShell {
    buildInputs = [
      persistence.packages.${system}.pythonWithPersistence
    ];
  };
}
```

### 3. 他のPythonプロジェクトでpersistenceモジュールを使用

```nix
{
  pythonEnv = pkgs.python312.withPackages (ps: [
    persistence.packages.${system}.persistenceModule
    # 他の依存関係
  ]);
}
```

## カスタマイズ方法

`flake.nix`の`customKuzu`セクションで拡張機能を追加できます：

```nix
customKuzu = pkgs.python312Packages.kuzu.overrideAttrs (oldAttrs: {
  postInstall = oldAttrs.postInstall or "" + ''
    # カスタム拡張機能のインストール
    ${pkgs.kuzu-extension}/bin/install-extension
  '';
});
```

## テスト実行

```bash
nix run .#test
```