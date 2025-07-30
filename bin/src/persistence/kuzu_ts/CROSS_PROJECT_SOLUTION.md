# kuzu_ts プロジェクト間利用の解決策

## 問題の本質

Worker実装は同一プロジェクト内では動作するが、他プロジェクトから利用する際に以下の問題が発生：

1. **Worker実行コンテキスト**: Workerは呼び出し元プロジェクトのコンテキストで実行される
2. **npm:kuzu依存**: sync/kuzu_tsプロジェクトにnpm:kuzuがないため、Worker内でimportが失敗
3. **モジュール解決**: node_modulesはプロジェクト境界を越えられない

## 解決策の比較

### 解決策A: 利用側でnpm:kuzuを追加 ⭐ 推奨

最もシンプルで確実な解決策。

```nix
# sync/kuzu_ts/flake.nix
devShells.default = pkgs.mkShell {
  buildInputs = with pkgs; [
    deno
    nodejs_20  # npm:kuzuのために追加
    stdenv.cc.cc.lib  # ネイティブ依存のために追加
    patchelf
  ];
  
  shellHook = ''
    # npm:kuzuをインストール
    ${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@0.10.0
    
    # ネイティブモジュールのパッチ
    for lib in node_modules/.deno/*/node_modules/kuzu/*.node; do
      [ -f "$lib" ] && ${pkgs.patchelf}/bin/patchelf --set-rpath "${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib]}" "$lib" || true
    done
  '';
};
```

**メリット**:
- 実装変更不要
- 各プロジェクトが明示的に依存を管理
- 既存のWorker実装をそのまま利用可能

**デメリット**:
- 各利用側でnpm:kuzuの設定が必要
- 重複した依存管理

### 解決策B: バンドル版の提供

persistence/kuzu_ts側でWorkerファイルをバンドルして提供。

```typescript
// persistence/kuzu_ts/build_bundled_worker.ts
import { bundle } from "https://deno.land/x/emit@0.40.0/mod.ts";

const result = await bundle("./core/kuzu_worker.ts", {
  compilerOptions: {
    inlineSourceMap: true,
  },
});

await Deno.writeTextFile("./dist/kuzu_worker.bundle.js", result.code);
```

```typescript
// persistence/kuzu_ts/mod_bundled.ts
export function createDatabaseBundled(path: string) {
  const workerCode = await Deno.readTextFile("./dist/kuzu_worker.bundle.js");
  const blob = new Blob([workerCode], { type: "application/javascript" });
  const worker = new Worker(URL.createObjectURL(blob), { type: "module" });
  // ...
}
```

**メリット**:
- 利用側の設定不要
- 依存関係を内包

**デメリット**:
- ビルドステップが必要
- バンドルサイズが大きい
- デバッグが困難

### 解決策C: Nixパッケージとして提供

flake.nixでパッケージとして提供し、利用側で参照。

```nix
# persistence/kuzu_ts/flake.nix
packages.default = pkgs.stdenv.mkDerivation {
  name = "kuzu-ts";
  src = ./.;
  
  buildPhase = ''
    # npm:kuzuを含む完全な環境を構築
    ${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@0.10.0
  '';
  
  installPhase = ''
    mkdir -p $out/lib
    cp -r * $out/lib/
    cp -r node_modules $out/lib/
  '';
};
```

**メリット**:
- Nix的に正しいアプローチ
- 再現性が高い

**デメリット**:
- 実装が複雑
- Deno哲学と相性が悪い

## 推奨事項

**解決策A（利用側でnpm:kuzu追加）を推奨**します。

理由：
1. **明示的な依存管理**: 各プロジェクトが使用する依存を明確に宣言
2. **実装の単純性**: 既存コードの変更不要
3. **Deno/Nix哲学との整合性**: 各プロジェクトが独立して依存を管理

## 実装例

sync/kuzu_tsでの実装例：

```nix
# flake.nix に追加
shellHook = ''
  # 既存の設定...
  
  # kuzu_ts Worker対応
  echo "Installing npm:kuzu for Worker support..."
  ${pkgs.deno}/bin/deno install --allow-scripts=npm:kuzu@0.10.0
  
  # ネイティブモジュールのパッチ
  export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
'';
```

これにより、sync/kuzu_tsからpersistence/kuzu_tsのWorker実装を問題なく利用できるようになります。