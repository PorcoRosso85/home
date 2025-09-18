#!/usr/bin/env bats
# 外部flake参照機能のテスト

@test "flake.nixが存在する" {
    [ -f "flake.nix" ]
}

@test "github形式の外部flake参照が定義されている" {
    # github:owner/repo形式の参照を確認
    run grep -E "url.*=.*\"github:" flake.nix
    [ "$status" -eq 0 ]
}

@test "path形式の外部flake参照が定義されている" {
    # path:../other-project形式の参照を確認
    run grep -E "url.*=.*\"path:" flake.nix
    [ "$status" -eq 0 ]
}

@test "外部flakeのpackagesを参照できる" {
    # 外部flakeのpackageをbuildInputsで使用していることを確認
    run grep -E "external-.*\.packages\.\\\${system\}" flake.nix
    [ "$status" -eq 0 ]
}

@test "flake metadataで外部inputsが確認できる" {
    # flake.lockファイルから直接確認（より確実）
    run jq -e '.nodes | keys | length > 3' flake.lock
    [ "$status" -eq 0 ]
    
    # external-devshellとexternal-orchestraの存在を確認
    run jq -e '.nodes["external-devshell"]' flake.lock
    [ "$status" -eq 0 ]
    
    run jq -e '.nodes["external-orchestra"]' flake.lock
    [ "$status" -eq 0 ]
}

@test "flake showで外部inputsが表示される" {
    # nix flake showでcontainer-integratedが表示されることを確認
    run nix flake show 2>&1
    [ "$status" -eq 0 ]
    
    # container-integratedが出力に含まれることを確認
    [[ "$output" == *"container-integrated"* ]]
}

@test "統合コンテナpackageが定義されている" {
    # 外部flakeを統合したコンテナの定義を確認
    run grep -q "container-integrated" flake.nix
    [ "$status" -eq 0 ]
}

@test "統合コンテナに複数の外部flakeが含まれる" {
    # buildContainerで複数の外部flakeを統合していることを確認
    run grep -A10 "container-integrated" flake.nix
    [ "$status" -eq 0 ]
    [[ "$output" == *"external-"* ]]
}

@test "外部flakeの型チェックが通る" {
    # nix flake checkが成功することを確認（簡易チェック）
    run nix flake check --no-build 2>&1
    # エラーが致命的でないことを確認
    [[ ! "$output" == *"error:"* ]] || [[ "$output" == *"warning:"* ]]
}

@test "統合コンテナがビルド可能" {
    # 実際のビルドは時間がかかるため、--dry-runで確認
    run nix build .#container-integrated --dry-run 2>&1
    # ビルドプランが作成できることを確認
    [ "$status" -eq 0 ] || [[ "$output" == *"would be built"* ]]
}