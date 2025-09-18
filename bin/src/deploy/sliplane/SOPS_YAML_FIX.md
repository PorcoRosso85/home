# .sops.yaml 修正案

## 現在の問題
path_regexが`.*env\.sh$`のため、env.sh.encにマッチしない

## 修正案

### Option 1: 両方にマッチする正規表現（推奨）
```yaml
# SOPS encryption rules for env files
creation_rules:
  - path_regex: .*env\.(sh|sh\.enc)$
    key_groups:
      - age:
          - age1xe09p4793xh9rptl3m7tdhxey5anc7erx8gau440ktt3qsknmq9q3nc3me
```

### Option 2: より汎用的なパターン
```yaml
# SOPS encryption rules for env files
creation_rules:
  - path_regex: .*env\.sh(\.enc)?$
    key_groups:
      - age:
          - age1xe09p4793xh9rptl3m7tdhxey5anc7erx8gau440ktt3qsknmq9q3nc3me
```

## 修正手順
```bash
# .sops.yamlを修正
vim .sops.yaml

# 既存の暗号化ファイルが正しく認識されるか確認
sops updatekeys env.sh.enc

# 動作確認
sops -d env.sh.enc | head -n 1
```

## 期待される効果
- env.shとenv.sh.enc両方が正しく認識される
- updatekeys操作が正常に動作
- チーム共有時の鍵追加が円滑