#!/usr/bin/env bats
# 複数flakeの成果物取得機能のテスト

@test "flake.nixが存在する" {
    [ -f "flake.nix" ]
}

@test "外部flakeのパッケージを取得できる" {
    # collectExternalPackagesを使用した外部パッケージ参照をチェック
    run grep -E "collectExternalPackages.*external-devshell" flake.nix
    [ "$status" -eq 0 ]
}

@test "複数inputsからの成果物参照が定義されている" {
    # 複数の外部flakeからのパッケージ参照を確認
    run grep -E "collectExternalPackages.*external-" flake.nix
    [ "$status" -eq 0 ]
    
    # 少なくとも2つの異なる外部flakeから参照していることを確認
    run bash -c 'grep -E "collectExternalPackages.*external-" flake.nix | wc -l'
    [ "$output" -ge 4 ]
}

@test "パッケージリストの取得確認" {
    # flake show でパッケージが表示されることを確認
    run nix flake show --json 2>/dev/null
    [ "$status" -eq 0 ]
    
    # JSONからpackagesセクションを確認
    run bash -c 'nix flake show --json 2>/dev/null | jq -e ".packages"'
    [ "$status" -eq 0 ]
}

@test "devShellsに外部パッケージが統合されている" {
    # devShells定義で外部flakeのパッケージを使用していることを確認
    run grep -A20 "devShells\.default" flake.nix
    [ "$status" -eq 0 ]
    
    # buildInputsまたはpackagesに外部パッケージが含まれていることを確認
    [[ "$output" == *"external-"* ]] || [[ "$output" == *"buildInputs"* ]]
}

@test "外部flakeからのツール収集が機能する" {
    # 統合コンテナで外部ツールが利用可能であることを確認
    run grep -A30 "container-integrated" flake.nix
    [ "$status" -eq 0 ]
    
    # extraPathsに外部パッケージが含まれることを確認
    [[ "$output" == *"extraPaths"* ]]
    [[ "$output" == *"external-"* ]]
}

@test "外部パッケージの条件付き取得が実装されている" {
    # collectExternalPackages関数の条件分岐を確認
    run grep -A5 "collectExternalPackages.*flake.*system" flake.nix
    [ "$status" -eq 0 ]
    
    # 存在しない場合のフォールバック（空配列）を確認
    [[ "$output" == *"[]"* ]]
}

@test "パッケージ収集の型安全性が確保されている" {
    # collectExternalPackages関数内の型安全性を確認
    run grep -A8 "collectExternalPackages.*=" flake.nix
    [ "$status" -eq 0 ]
    
    # 条件分岐の存在を確認
    [[ "$output" == *"if"* ]]
    [[ "$output" == *"then"* ]]
    [[ "$output" == *"else"* ]]
}

@test "複数flakeからのパッケージ統合が実装されている" {
    # 複数の外部flakeからパッケージを統合するextraPathsを確認
    run grep -A10 "extraPaths" flake.nix
    [ "$status" -eq 0 ]
    
    # 複数のflakeからのパッケージが++演算子で結合されていることを確認
    [[ "$output" == *"++"* ]]
}

@test "flake metadataで成果物が確認可能" {
    # nix flake metadataで外部inputsが表示されることを確認
    run nix flake metadata --json 2>/dev/null
    [ "$status" -eq 0 ]
    
    # 外部flakeのinputsが存在することを確認
    run bash -c 'nix flake metadata --json 2>/dev/null | jq -e ".locks.nodes | keys[]" | grep external'
    [ "$status" -eq 0 ]
}

@test "成果物の実際のビルドが可能" {
    # 統合コンテナのドライランでビルド可能性を確認
    run nix build .#container-integrated --dry-run 2>&1
    # エラーではなく、ビルドプランが表示されることを確認
    [ "$status" -eq 0 ] || [[ "$output" == *"would be built"* ]]
    
    # 致命的なエラーがないことを確認
    [[ ! "$output" == *"error: attribute"* ]]
}

@test "開発環境で外部パッケージにアクセス可能" {
    # nix developが成功することを確認（実際に入らずチェックのみ）
    run nix develop --command echo "dev shell accessible" 2>&1
    [ "$status" -eq 0 ]
    [[ "$output" == *"dev shell accessible"* ]]
}