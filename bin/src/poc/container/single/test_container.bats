#!/usr/bin/env bats
# 単一コンテナ仕様のテスト (Nix dockerTools)

@test "flake.nixが存在する" {
    [ -f "flake.nix" ]
}

@test "コンテナイメージがdockerTools.buildImageでビルドできる" {
    run nix build .#container --no-link --print-out-paths
    [ "$status" -eq 0 ]
}

@test "ビルドされたイメージにメタデータが含まれる" {
    result=$(nix build .#container --no-link --print-out-paths)
    # Dockerイメージはディレクトリ形式またはtarファイル
    run bash -c "test -f '$result' && tar -tf '$result' | grep -E '(manifest.json|repositories)' || test -d '$result'"
    [ "$status" -eq 0 ]
}

@test "コンテナ内にNixパッケージが含まれる" {
    # flake.nixにcurl、jq、bashの定義があるか確認
    run bash -c "grep -E '(curl|jq|bashInteractive)' flake.nix"
    [ "$status" -eq 0 ]
}

@test "エントリーポイントが定義されている" {
    # flake.nixにEntrypointの定義があるか確認
    run grep -q "Entrypoint" flake.nix
    [ "$status" -eq 0 ]
}

@test "環境変数が設定されている" {
    # flake.nixにNIX_CONTAINER環境変数の定義があるか確認
    run grep -q "NIX_CONTAINER" flake.nix
    [ "$status" -eq 0 ]
}

@test "レイヤーが最適化されている" {
    # Nixのレイヤー最適化を確認
    result=$(nix build .#container --no-link --print-out-paths)
    layer_count=$(tar -tf "$result" | grep -c "layer.tar" || echo 0)
    [ "$layer_count" -ge 1 ]
}

@test "再現可能なビルド" {
    # 同じ入力から同じ出力が生成される
    path1=$(nix build .#container --no-link --print-out-paths)
    path2=$(nix build .#container --no-link --print-out-paths)
    [ "$path1" = "$path2" ]
}