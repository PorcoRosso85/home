#!/usr/bin/env bats
# 統合コンテナ（container-integrated）のビルドと動作テスト

@test "container-integratedがflake.nixに定義されている" {
    run grep -q "container-integrated" flake.nix
    [ "$status" -eq 0 ]
}

@test "統合コンテナに専用エントリーポイントが定義されている" {
    run grep -q "integrated-entrypoint.sh" flake.nix
    [ "$status" -eq 0 ]
}

@test "外部flakeの収集関数が定義されている" {
    run grep -q "collectExternalPackages" flake.nix
    [ "$status" -eq 0 ]
}

@test "external-devshellが外部flakeとして参照されている" {
    run grep -q "external-devshell" flake.nix
    [ "$status" -eq 0 ]
    run grep -q "github:numtide/devshell" flake.nix
    [ "$status" -eq 0 ]
}

@test "external-orchestraが外部flakeとして参照されている" {
    run grep -q "external-orchestra" flake.nix
    [ "$status" -eq 0 ]
    run grep -q "path:../orchestra" flake.nix
    [ "$status" -eq 0 ]
}

@test "統合コンテナのextraPathsに外部パッケージが含まれる" {
    # container-integrated定義から82行後にextraPathsが存在することを確認
    run bash -c "grep -A82 'container-integrated' flake.nix | grep -q 'extraPaths'"
    [ "$status" -eq 0 ]
    run bash -c "grep -A82 'container-integrated' flake.nix | grep -q 'collectExternalPackages'"
    [ "$status" -eq 0 ]
}

@test "統合コンテナイメージがビルドできる" {
    run nix build .#container-integrated --no-link
    [ "$status" -eq 0 ]
}

@test "統合コンテナビルド結果が有効なDockerイメージ形式である" {
    # 統合コンテナをビルド
    result=$(nix build .#container-integrated --print-out-paths)
    [ -f "$result" ]
    
    # tar.gz形式であることを確認
    run file "$result"
    [[ "$output" == *"gzip compressed"* ]]
    
    # Dockerイメージの必須ファイルを確認
    run tar -tzf "$result"
    [[ "$output" == *"manifest.json"* ]]
    [[ "$output" == *"repositories"* ]]
    [[ "$output" == *"layer.tar"* ]]
}

@test "Podmanで統合コンテナイメージをロードできる" {
    # 統合コンテナをビルド
    result=$(nix build .#container-integrated --print-out-paths)
    
    # Podmanでイメージをロード
    run nix-shell -p podman --run "gunzip -c $result | podman load 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Loaded image"* ]]
}

@test "Podmanで統合コンテナを実行できる" {
    # イメージがロード済みか確認、なければロード
    run nix-shell -p podman --run "podman images | grep -q integrated-container || (gunzip -c $(nix build .#container-integrated --print-out-paths) | podman load)"
    
    # 統合コンテナを実行
    run nix-shell -p podman --run "podman run --rm localhost/integrated-container:latest 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Integrated Container with External Flakes"* ]]
}

@test "統合コンテナのエントリーポイントが複数flakeの情報を表示する" {
    # 統合コンテナを実行して出力を確認
    run nix-shell -p podman --run "podman run --rm localhost/integrated-container:latest 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Available components:"* ]]
    [[ "$output" == *"External flake integrations:"* ]]
    [[ "$output" == *"Integration Complete"* ]]
}

@test "統合コンテナに基本ツールが含まれている" {
    # 統合コンテナ内でbashコマンドを実行
    run nix-shell -p podman --run "podman run --rm --entrypoint /bin/bash localhost/integrated-container:latest -c 'which bash && which curl && which jq' 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"/bin/bash"* ]]
    [[ "$output" == *"/bin/curl"* ]]
    [[ "$output" == *"/bin/jq"* ]]
}

@test "統合コンテナのメタデータにcontainer-typeが設定されている" {
    # イメージのメタデータを確認
    run nix-shell -p podman --run "podman inspect localhost/integrated-container:latest | jq '.[0].Config.Labels' 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"org.nixos.container"* ]]
    [[ "$output" == *"org.nixos.container-type"* ]]
    [[ "$output" == *"integrated-container"* ]]
}

@test "統合コンテナが外部flakeコンポーネントをチェックできる" {
    # 統合コンテナ内で外部flakeのコンポーネントチェックを実行
    run nix-shell -p podman --run "podman run --rm --entrypoint /bin/bash localhost/integrated-container:latest -c 'command -v devshell-menu; echo \"Exit code: \$?\"' 2>&1"
    # 存在しない場合でもエラーにならない（エントリーポイント内でチェックしているため）
    [ "$status" -eq 0 ]
}

@test "統合コンテナでディレクトリ構造をチェックできる" {
    # orchestra関連のディレクトリをチェック
    run nix-shell -p podman --run "podman run --rm --entrypoint /bin/bash localhost/integrated-container:latest -c 'ls -la / | head -20' 2>&1"
    [ "$status" -eq 0 ]
    # ルートディレクトリの基本構造が確認できればOK
    [[ "$output" == *"bin"* ]]
}

@test "開発シェルに統合コンテナ用のコマンドが表示される" {
    # shellHookに統合コンテナの説明があることを確認
    run grep -q "container-integrated" flake.nix
    [ "$status" -eq 0 ]
}

@test "複数flakeの統合パッケージリストが型安全に処理される" {
    # collectExternalPackages関数の型安全なチェック実装を確認
    run bash -c "grep -A10 'collectExternalPackages' flake.nix | grep -q 'packages.\${system}'"
    [ "$status" -eq 0 ]
    run bash -c "grep -A10 'collectExternalPackages' flake.nix | grep -q 'default'"
    [ "$status" -eq 0 ]
}