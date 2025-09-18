#!/usr/bin/env bats
# 単一flakeからの複数コンテナタイプビルドテスト

@test "flake.nixが存在する" {
    [ -f "flake.nix" ]
}

@test "複数のコンテナタイプが内部定義されている" {
    # nodejsApp、pythonApp、goAppが定義されているか確認
    run grep -q "nodejsApp =" flake.nix
    [ "$status" -eq 0 ]
    
    run grep -q "pythonApp =" flake.nix
    [ "$status" -eq 0 ]
    
    run grep -q "goApp =" flake.nix
    [ "$status" -eq 0 ]
}

@test "複数のコンテナタイプがビルド可能" {
    # 基本コンテナ
    run grep -q "container-base" flake.nix
    [ "$status" -eq 0 ]
    
    # Node.jsコンテナ
    run grep -q "container-nodejs" flake.nix
    [ "$status" -eq 0 ]
    
    # Pythonコンテナ
    run grep -q "container-python" flake.nix
    [ "$status" -eq 0 ]
    
    # Goコンテナ
    run grep -q "container-go" flake.nix
    [ "$status" -eq 0 ]
}

@test "flake-selectorアプリが定義されている" {
    run grep -q "apps.flake-selector" flake.nix
    [ "$status" -eq 0 ]
}

@test "各コンテナタイプに適切なランタイムが含まれる" {
    # Node.jsランタイム
    run bash -c "grep -A5 'container-nodejs' flake.nix | grep -E 'nodejs|nodejs_20'"
    [ "$status" -eq 0 ]
    
    # Pythonランタイム
    run bash -c "grep -A5 'container-python' flake.nix | grep -E 'python|python3'"
    [ "$status" -eq 0 ]
    
    # Goランタイム
    run bash -c "grep -A5 'container-go' flake.nix | grep 'go'"
    [ "$status" -eq 0 ]
}

@test "buildContainer関数が定義されている" {
    # 共通のビルド関数で複数のコンテナを構築
    run grep -q "buildContainer =" flake.nix
    [ "$status" -eq 0 ]
}

@test "各コンテナにラベルが設定されている" {
    # container-typeラベルが設定されているか
    run grep -q "org.nixos.container-type" flake.nix
    [ "$status" -eq 0 ]
}

@test "基本コンテナイメージがビルドできる" {
    run nix build .#container-base --no-link
    [ "$status" -eq 0 ]
}

@test "Node.jsコンテナイメージがビルドできる" {
    run nix build .#container-nodejs --no-link
    [ "$status" -eq 0 ]
}

@test "Pythonコンテナイメージがビルドできる" {
    run nix build .#container-python --no-link
    [ "$status" -eq 0 ]
}

@test "Goコンテナイメージがビルドできる" {
    run nix build .#container-go --no-link
    [ "$status" -eq 0 ]
}

@test "コンテナ選択スクリプトが実行可能" {
    # flake-selectorが実行可能な形式で定義されているか
    run grep -q "type = \"app\"" flake.nix
    [ "$status" -eq 0 ]
    run grep -q "program =" flake.nix
    [ "$status" -eq 0 ]
}

@test "開発シェルにbatsが含まれる" {
    run grep -q "bats" flake.nix
    [ "$status" -eq 0 ]
}

@test "各コンテナにエントリーポイントが設定されている" {
    run grep -q "Entrypoint =" flake.nix
    [ "$status" -eq 0 ]
}

@test "環境変数NIX_CONTAINERが設定されている" {
    run grep -q "NIX_CONTAINER=true" flake.nix
    [ "$status" -eq 0 ]
}

# Podmanによる実際のコンテナ動作検証

@test "ビルド結果が有効なDockerイメージ形式である" {
    # 基本コンテナをビルド
    result=$(nix build .#container-base --print-out-paths)
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

@test "Podmanで基本コンテナイメージをロードできる" {
    # コンテナをビルド
    result=$(nix build .#container-base --print-out-paths)
    
    # Podmanでイメージをロード
    run nix-shell -p podman --run "gunzip -c $result | podman load 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Loaded image"* ]]
}

@test "Podmanで基本コンテナを実行できる" {
    # イメージがロード済みか確認、なければロード
    run nix-shell -p podman --run "podman images | grep -q base-container || (gunzip -c $(nix build .#container-base --print-out-paths) | podman load)"
    
    # コンテナを実行
    run nix-shell -p podman --run "podman run --rm localhost/base-container:latest 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Single Flake Multi-Container Builder"* ]]
}

@test "PodmanでNode.jsコンテナをロードして実行できる" {
    # コンテナをビルド
    result=$(nix build .#container-nodejs --print-out-paths)
    
    # Podmanでロードと実行
    run nix-shell -p podman --run "gunzip -c $result | podman load 2>&1"
    [ "$status" -eq 0 ]
    
    run nix-shell -p podman --run "podman run --rm localhost/nodejs-container:latest 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Node.js Application Container"* ]]
    [[ "$output" == *"Node version:"* ]]
}

@test "PodmanでPythonコンテナをロードして実行できる" {
    # コンテナをビルド
    result=$(nix build .#container-python --print-out-paths)
    
    # Podmanでロードと実行
    run nix-shell -p podman --run "gunzip -c $result | podman load 2>&1"
    [ "$status" -eq 0 ]
    
    run nix-shell -p podman --run "podman run --rm localhost/python-container:latest 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Python Application Container"* ]]
    [[ "$output" == *"Python version:"* ]]
}

@test "PodmanでGoコンテナをロードして実行できる" {
    # コンテナをビルド
    result=$(nix build .#container-go --print-out-paths)
    
    # Podmanでロードと実行
    run nix-shell -p podman --run "gunzip -c $result | podman load 2>&1"
    [ "$status" -eq 0 ]
    
    run nix-shell -p podman --run "podman run --rm localhost/go-container:latest 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Go Application Container"* ]]
    [[ "$output" == *"Go version:"* ]]
}

@test "コンテナ内で各ランタイムが正しく動作する" {
    # Node.jsコンテナでJavaScriptコードを実行（エントリーポイントをオーバーライド）
    run nix-shell -p podman --run "podman run --rm --entrypoint /bin/bash localhost/nodejs-container:latest -c 'echo \"console.log(1+1)\" | node' 2>&1"
    [[ "$output" == *"2"* ]]
    
    # Pythonコンテナでコードを実行（エントリーポイントをオーバーライド）
    run nix-shell -p podman --run "podman run --rm --entrypoint /bin/bash localhost/python-container:latest -c 'echo \"print(1+1)\" | python3' 2>&1"
    [[ "$output" == *"2"* ]]
}

@test "Podmanでロードしたイメージの情報を確認できる" {
    # イメージ一覧に表示される
    run nix-shell -p podman --run "podman images --format '{{.Repository}}' | grep container"
    [ "$status" -eq 0 ]
    [[ "$output" == *"base-container"* ]]
    
    # イメージのメタデータを確認
    run nix-shell -p podman --run "podman inspect localhost/base-container:latest | jq '.[0].Config.Labels' 2>&1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"org.nixos.container"* ]]
    [[ "$output" == *"org.nixos.container-type"* ]]
}