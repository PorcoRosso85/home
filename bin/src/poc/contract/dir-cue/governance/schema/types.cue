package schema

// #DirContract は方針のみを定義する閉構造
// 責務分離の原則：dir.cueは方針のみ、実装語（API名、テーブル名等）は禁止
// close()により未定義フィールド追加を型レベルで防止
#DirContract: close({
	// 必須フィールド群
	srp: string & =~"^.{1,80}$" // 単一責務原則記述（80字制限）
	goals: [...string] // プロジェクト目標（空配列可）
	nonGoals: [...string] // 明示的な非目標（空配列可）

	// 任意フィールド群
	owner?:       string & =~"^.+$"                       // 所有者識別子（空文字禁止）
	domain_path?: string & =~"^[a-z0-9.-]+/[a-z0-9-./]+$" // ドメイン階層パス
})

// #FlakeContract は境界のみを定義する閉構造
// 責務分離の原則：flake.nixは技術境界のみ、方針はdir.cueに委譲
// close()により意図しない技術詳細の混入を防止
#FlakeContract: close({
	// 必須フィールド群
	role:  "app" | "lib" | "service" | "tool" | "infra" // flakeタイプ（閉集合）
	owner: string & =~"^.+$"                            // 責任者識別子（空文字禁止）

	// 対外提供インターフェース（約束座標）
	exports: [...#Export]

	// 外部flake依存関係（inputs管理）
	dependsOn: [...#DepRef]
})

// #Export は対外提供インターフェースを定義する閉構造
// 目的：flakeが外部に約束するインターフェース座標を型安全に管理
// close()により未定義プロトコルタイプの追加を防止
#Export: close({
	// 必須フィールド：インターフェース種別
	kind: "http" | "grpc" | "db" | "cli" | "api" | "lib" | "service" // プロトコル種別（閉集合）

	// 任意フィールド：詳細仕様
	id?:          string & =~"^.+$"                                                     // エクスポート識別子
	uri?:         string & =~"^.+$"                                                     // エンドポイントURI
	version?:     string & =~"^\\d+\\.\\d+\\.\\d+(-[0-9A-Za-z-]+)*(\\+[0-9A-Za-z-]+)*$" // セマンティックバージョニング
	protocol?:    "tcp" | "https" | "http" | "grpc" | "unix"                            // 通信プロトコル（閉集合）
	scope?:       "public" | "internal"                                                 // 公開範囲（閉集合）
	port?:        int & >=1 & <=65535                                                   // ポート番号（1-65535）
	description?: string & =~"^.+$"                                                     // インターフェース説明
})

// #DepRef は依存関係を定義する閉構造
// 目的：flakeの外部依存を型安全に管理し、inputs制約を強制
// close()により予期しない依存タイプの追加を防止
#DepRef: close({
	// 必須フィールド：依存関係の基本情報
	kind:   "http" | "grpc" | "db" | "cli" | "api" | "lib" | "service" // 依存インターフェース種別（閉集合）
	target: string & =~"^.+$"                                          // 依存先識別子（例: namespace/name, flakeRef）

	// 任意フィールド：依存関係の詳細仕様
	id?:           string & =~"^.+$" // 依存識別子（ローカル参照用）
	versionRange?: string & =~"^.+$" // バージョン制約（例: "^1.2.0", ">=2.0.0"）
	optional?:     bool              // オプショナル依存フラグ
	description?:  string & =~"^.+$" // 依存理由・用途説明
})
