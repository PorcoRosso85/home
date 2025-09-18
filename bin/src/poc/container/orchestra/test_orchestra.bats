#!/usr/bin/env bats
# オーケストレーション仕様のテスト (arion/nixos-container)

@test "flake.nixが存在する" {
    [ -f "flake.nix" ]
}

@test "arion設定が定義されている" {
    run grep -q "arionProject" flake.nix
    [ "$status" -eq 0 ]
}

@test "複数のサービスが定義されている" {
    # web, api, dbの3つのサービスを確認
    run bash -c "grep -oE '(web =|api =|db =)' flake.nix | sort -u | wc -l"
    [ "$output" -ge 3 ]
}

@test "各サービスのコンテナイメージがビルドできる" {
    run nix build .#web-container --no-link
    [ "$status" -eq 0 ]
    run nix build .#api-container --no-link
    [ "$status" -eq 0 ]
    run nix build .#db-container --no-link
    [ "$status" -eq 0 ]
}

@test "ネットワーク設定が定義されている" {
    run grep -q "networks" flake.nix
    [ "$status" -eq 0 ]
}

@test "ボリューム設定が定義されている" {
    run grep -q "volumes" flake.nix
    [ "$status" -eq 0 ]
}

@test "サービス間の依存関係が定義されている" {
    # apiサービスがdbに依存しているか確認
    run grep -q "depends_on.*db" flake.nix
    [ "$status" -eq 0 ]
}

@test "環境変数が設定されている" {
    run grep -q "DATABASE_URL" flake.nix
    [ "$status" -eq 0 ]
}

@test "ヘルスチェックが設定されている" {
    run grep -q "healthcheck" flake.nix
    [ "$status" -eq 0 ]
}

@test "arion docker-compose.yml生成ができる" {
    # arion appが定義されているか確認
    run grep -q "apps.arion" flake.nix
    [ "$status" -eq 0 ]
}

@test "nixos-container定義も存在する" {
    # 代替手段としてnixos-containerも定義
    run grep -q "nixosConfigurations.container-cluster" flake.nix
    [ "$status" -eq 0 ]
}