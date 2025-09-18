#!/usr/bin/env bats

setup() {
  export TEST_DIR=$(mktemp -d)
  mkdir -p "$TEST_DIR/src"
  touch "$TEST_DIR/src/main.py" "$TEST_DIR/src/utils.py"
}

teardown() {
  rm -rf "$TEST_DIR"
}

@test "missing files are detected" {
  result=$(echo '[{"uri":"file://'$TEST_DIR'/src/main.py"},{"uri":"file://'$TEST_DIR'/src/missing.py"}]' | nix run . -- "$TEST_DIR/src")
  [[ "$result" == *'"path":"'$TEST_DIR'/src/missing.py","status":"missing"'* ]]
}

@test "unspecified files are detected" {
  result=$(echo '[{"uri":"file://'$TEST_DIR'/src/main.py"}]' | nix run . -- "$TEST_DIR/src")
  [[ "$result" == *'"path":"'$TEST_DIR'/src/utils.py","status":"unspecified"'* ]]
}

@test "fragments are stripped from URIs" {
  result=$(echo '[{"uri":"file://'$TEST_DIR'/src/main.py#L42"}]' | nix run . -- "$TEST_DIR/src")
  [[ "$result" != *"#L42"* ]]
}

@test "hidden files are ignored" {
  touch "$TEST_DIR/src/.hidden"
  result=$(echo '[]' | nix run . -- "$TEST_DIR/src")
  [[ "$result" != *".hidden"* ]]
}

@test "empty input produces only unspecified files" {
  result=$(echo '[]' | nix run . -- "$TEST_DIR/src")
  [[ "$result" == *'"status":"unspecified"'* ]]
  [[ "$result" != *'"status":"missing"'* ]]
}