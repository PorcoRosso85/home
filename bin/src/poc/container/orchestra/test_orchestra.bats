#!/usr/bin/env bats
# オーケストレーション仕様のテスト (arion/nixos-container)

@test "flake.nixが存在する" {
    [ -f "flake.nix" ]
}

@test "arion設定が定義されている" {
    run nix eval .#arionProject --json
    [ "$status" -eq 0 ]
}

@test "複数のサービスが定義されている" {
    # web, api, dbの3つのサービスを確認
    run nix eval .#arionProject.services --apply 'builtins.attrNames' --json
    [ "$status" -eq 0 ]
    [[ "$output" =~ "web" ]]
    [[ "$output" =~ "api" ]]
    [[ "$output" =~ "db" ]]
}

@test "各サービスのコンテナイメージがビルドできる" {
    run nix build .#containers.web --no-link
    [ "$status" -eq 0 ]
    run nix build .#containers.api --no-link
    [ "$status" -eq 0 ]
    run nix build .#containers.db --no-link
    [ "$status" -eq 0 ]
}

@test "ネットワーク設定が定義されている" {
    run nix eval .#arionProject.networks --json
    [ "$status" -eq 0 ]
    [[ "$output" != "null" ]]
}

@test "ボリューム設定が定義されている" {
    run nix eval .#arionProject.volumes --json
    [ "$status" -eq 0 ]
    [[ "$output" != "null" ]]
}

@test "サービス間の依存関係が定義されている" {
    # apiサービスがdbに依存しているか確認
    run nix eval .#arionProject.services.api.depends_on --json
    [ "$status" -eq 0 ]
    [[ "$output" =~ "db" ]]
}

@test "環境変数が設定されている" {
    run nix eval .#arionProject.services.api.environment --json
    [ "$status" -eq 0 ]
    [[ "$output" =~ "DATABASE_URL" ]]
}

@test "ヘルスチェックが設定されている" {
    run nix eval .#arionProject.services.api.healthcheck --json
    [ "$status" -eq 0 ]
    [[ "$output" != "null" ]]
}

@test "arion docker-compose.yml生成ができる" {
    run nix run .#arion -- config
    [ "$status" -eq 0 ]
    [[ "$output" =~ "version:" ]]
}

@test "nixos-container定義も存在する" {
    # 代替手段としてnixos-containerも定義
    run nix eval .#nixosConfigurations.container-cluster --apply 'x: x?config' 
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}