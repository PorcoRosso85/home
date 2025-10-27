# contracts-index flake

## 責務
- manifest.cue群からcapsules/index.cueを決定的に生成
- 生成規約/決定性/しきい値の管理

## 生成ルール
- 安定ソート + `cue fmt`
- `genVersion`/`genHash` 埋め込み
- 同一 flake.lock でバイト等価を保証
