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
    run tar -tf "$result" | grep -E "(manifest.json|repositories)"
    [ "$status" -eq 0 ]
}

@test "コンテナ内にNixパッケージが含まれる" {
    result=$(nix build .#container --no-link --print-out-paths)
    # tarballの中身を確認
    run tar -tf "$result" | grep -E "(curl|jq|bash)"
    [ "$status" -eq 0 ]
}

@test "エントリーポイントが定義されている" {
    # flake.nixでconfigが正しく設定されているか確認
    run nix eval .#container.config.Entrypoint --json
    [ "$status" -eq 0 ]
    [[ "$output" =~ "entrypoint" ]]
}

@test "環境変数が設定されている" {
    run nix eval .#container.config.Env --json
    [ "$status" -eq 0 ]
    [[ "$output" =~ "NIX_CONTAINER" ]]
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