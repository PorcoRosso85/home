# Reliability Conventions

## 責務
ゲート/指標/運用の信頼性基準

## しきい値
- `gen-index`: ≤10s/repo
- `lint contracts`: ≤5s/PR
- `capsules/index.cue`: ≤256KB

## CI DoD
1. `nix build .#contracts-index`
2. `nix run .#gate -- lint --all`
3. `nix run .#gate -- lint contracts`
4. `nix run .#gate -- plan --changed-only`
5. `nix run .#gate -- smoke`

上記すべて0終了 + index決定的生成
