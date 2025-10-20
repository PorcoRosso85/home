// 責務: manifest.cue群 → capsules/index.cue 生成
// MUST: 安定ソート + cue fmt + genVersion/genHash 埋め込み
// MUST: 孤児/重複URI検出
// しきい値: ≤10s/repo、index.cue ≤256KB
package cmds
