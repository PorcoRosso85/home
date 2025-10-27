# ADR 0.10.12: Orchestration v4.1b — URI徹底 / 薄いGW / DB書込=WFのみ / SA最小4キー / 構成統一リファクタ

- **ID**: adr-0.10.12 (251023-orch-v4.1b)
- **Date**: 2025-10-23 (JST)
- **Status**: Superseded
- **Superseded by**: adr-0.11.0
- **Owners**: Orchestration / Gateway / Temporal
- **Scope**: Gateway・Workflow/Worker・Search Attributes・SSOT・ディレクトリ構成（監査は除外）

> **Note**: この ADR は adr-0.11.0 により Superseded されました。構成は4層アーキテクチャに再配置されています。履歴参照用に保持。

---

## 0. 要約

- **URI徹底**: クライアント入力は `uri`（例 `fs://<space-id>/path`）のみ
- **薄いGW**: `opencode serve` の**オンデマンド起動**・**逆プロキシ**・**内部API(2本)**のみ
- **DB書込=WFのみ**: 業務DB(SSOT)は Workflow/Activity **だけ**が書く。GWは**無状態**（揮発Mapのみ）
- **冪等**: `workflowId = hash(uri + request-hash + role-id)` + `RejectDuplicate`。置換は明示時のみ
- **SA最小4キー**（kebab-case固定・拡張なし）: `space-id` / `corr-id` / `stage-no` / `run-state`
- **構成統一リファクタ**:
  - `features/opencode-autopilot` に**フラット化**（余分層削除）
  - `deployables/*` は **DDD3層（application/domain/infrastructure）**直下。`src/` を廃止
  - **契約/ポリシ/CUE**は現行維持、禁止事項を明文化

---

## 1. 背景

- これまでの合意: URI徹底・薄いGW・WFでSLA/冪等・SA4キー
- 懸念: `deployables` と `features` の階層不統一、`src/` 層の過剰、`features/orchestration/…` の余分層

---

## 2. 決定（技術方針）

### GW（Gateway）

- **責務**: URI正規化/認可 → **起動**（ensureInstance）→ **逆プロキシ** → **内部API**（`opencode/ensure`, `wf/task-completed`）
- **状態**: `Map<uri,{pid,port,lastAccess}>` の**揮発のみ**。TTL/LRU。永続DBは触らない
- **置換**: `replace: true` のときのみ `TerminateIfRunning → Start`

### WF/Worker

- **WF**: `signalWithStart(workflowId)`、SLAタイマー、`ACK/SNOOZE/CANCEL/taskCompleted`
- **SA**: `setStage()` に**一極化**（`upsertSearchAttributes`はここだけ）
- **Worker(Activity)**: 外部I/OはGWの内部API経由。完了は `task-completed` を**冪等**送信

### SSOT（libsql/Turso）

- **WFのみ書込**。最小DDL: `runs / events / kpi`
- `workflowId/corr-id/request-hash` は **JCS(JSON正規化)→SHA-256**で揃える

### Search Attributes（登録済み前提）

- `space-id:Keyword`, `corr-id:Keyword`, `stage-no:Int`, `run-state:Keyword`
- 遷移: 0→受付、1→進行、2→待ち、3→完了／置換時は `REPLACED`

### API最小

- **外部 `/api`**: `POST /jobs/start`、`POST /sessions/:id/(ack|snooze|cancel)`、`GET /jobs/:id/status`
- **内部 `/internal`**: `POST /opencode/ensure`、`POST /wf/task-completed` の**2本のみ**

---

## 3. ディレクトリ構成（統一ルール）

- **命名**: kebab-case
- **単位**: **1 feature = 1 flake**、**1 deployable = 1 flake**
- **階層**: 直下に **`application/` `domain/` `infrastructure/`** のみ（空なら `.gitkeep`）
- **禁止**: `src/` 常設、余分な中間層（例: `features/orchestration/`）
- **CUEポリシ**に禁止事項を明記:
  - **dirPath禁止（URI必須）**
  - **SAキーは4つのみ**
  - **GWのDB書込は禁止**

---

## 4. 代替案と却下理由

- `src/` 層存続: KISS/YAGNIに反し階層が増えるため却下
- `features/orchestration/…` 維持: スコープ曖昧・DRY違反の芽→削除
- GWで冪等キーのDB管理: **DB単一書込主体**に反するため却下

---

## 5. リスク / 対策

- 初回起動レイテンシ → プリウォーム枠／常駐数上限
- SA将来拡張 → 当面4キー固定、詳細はMemoへ
- GW障害 → 無状態のため再起動容易。多重化で緩和

---

## 6. 完了条件（DoD）

1. クライアント入力は `uri` のみ
2. GWは**揮発のみ**で OpenCode をオンデマンド起動・逆プロキシ可能
3. **WFのみ**がSSOTへ書込（E2Eで確認）
4. **SA4キー**が登録・更新される（`setStage()`一極化）
5. **ディレクトリ構成が統一**（features/deployables とも DDD3層直下、`src/`不使用）
6. CI green（fs://最短経路E2E、CUEポリシFailなし）

---

## 7. 参照アーキテクチャ

### 主要構成要素

```
repo/
├─ features/
│  └─ opencode-autopilot/              # フラット化（余分層削除）
│     ├─ flake.nix
│     ├─ application/
│     │  ├─ workflow.go                # WF本体/SA setStage一極化
│     │  └─ manifest.cue               # WF契約(SA=4,queue,timeout)
│     ├─ domain/
│     │  ├─ types.go                   # uri/corr-id/value objects
│     │  └─ policy.go                  # SLA段階/閾値
│     └─ infrastructure/
│        └─ ssotrepo/libsql.go         # 唯一の業務DB書込口(WFのみ使用)
├─ deployables/
│  ├─ opencode-gateway/                # src廃止：DDD3層直下
│  │  ├─ flake.nix
│  │  ├─ manifest.cue
│  │  ├─ application/
│  │  │  ├─ main.go                    # HTTP起動(/api,/internal)
│  │  │  └─ wiring.go                  # DI/設定/ルータ配線
│  │  ├─ domain/
│  │  │  └─ .gitkeep                   # 先行で空層を確保（必要時のみ実装）
│  │  └─ infrastructure/
│  │     ├─ ensure.go                  # ensureInstance(uri)/TTL/LRU
│  │     └─ proxy.go                   # /w/:wsId/* → OpenCode 逆プロキシ
│  └─ opencode-worker/
│     ├─ flake.nix
│     ├─ manifest.cue
│     ├─ application/
│     │  ├─ main.go                    # Worker起動/metrics
│     │  ├─ register.go                # WF/Activity登録
│     │  └─ activities.go              # /internal 呼出し/冪等送信
│     ├─ domain/
│     │  └─ .gitkeep
│     └─ infrastructure/
│        └─ .gitkeep
└─ platform/
   ├─ temporal/
   │  ├─ search-attributes.hcl         # SA=4キー(kebab-case)
   │  ├─ namespace.sh                  # Namespace/SA 初期化
   │  ├─ docker-compose.dev.yml        # dev: server+ui
   │  └─ README.md                     # 登録手順/注意
   └─ libsql/
      ├─ docker-compose.dev.yml        # ローカル sqld
      ├─ migrate.sh                    # migrations 適用
      └─ migrations/
         ├─ 0001_init.sql              # runs/events/kpi 基本
         └─ 0002_kpi.sql               # KPI拡張
```

---

## 8. CUEポリシ禁止事項（policy/cue/rules/strict.cue）

```cue
// URI必須（dirPath禁止）
#RequireURI: {
    input: "uri" | "resource_uri" | "target_uri"
    _forbidden: ["dirPath", "dir_path", "directory"]
}

// SA4キー固定（拡張禁止）
#SearchAttributesFixed: {
    allowed: ["space-id", "corr-id", "stage-no", "run-state"]
    _forbidden: [string]: never
}

// GWのDB書込禁止
#GatewayNoDBWrite: {
    component: "gateway" | "opencode-gateway"
    _forbidden_operations: ["INSERT", "UPDATE", "DELETE", "MERGE"]
    _allowed: ["SELECT"] // 読み取りのみ
}
```

---

## 9. 関連ADR

- **ADR 0.10.8**: SSOT-first & thin manifest（契約管理の基礎）
- **ADR 0.10.10**: Flake-driven manifest（決定的生成）
- **ADR 0.10.11**: consumes/Secrets/SBOM/CVE（セキュリティ強化）
- **ADR 0.10.12**: 本ADR（Orchestration具体実装 + 構成統一）
