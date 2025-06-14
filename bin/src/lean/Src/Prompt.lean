def screenBase := "
目的は以下のmain処理をもつshファイルを作成することである
shファイルを実行した結果, 指定ディレクトリについてscreenセッションが用意され、各セッション指定ディレクトリのflake.nixファイルによる仮想環境に入った状態での左右ウィンドウを用意しているはずである

main処理は指定リポジトリパス配列を受け付ける、リポジトリパスはローカルの場合ディレクトリパスである
main処理は上記を受け付けて、各パスについて以下を実施する
指定レイアウトである左右分割状態でセッション 'path_to_dir' を開始する
左右それぞれで 'nix develop' コマンドが実行される

"

def tmuxBaseSession := "
目的は以下のmain処理をもつshファイルを作成することである
shファイルを実行した結果, 指定ディレクトリについてtmuxセッションが用意され、各セッション指定ディレクトリのflake.nixファイルによる仮想環境に入った状態での左右ウィンドウを用意しているはずである

main処理は指定リポジトリパス配列を受け付ける、リポジトリパスはローカルの場合ディレクトリパスである
main処理は上記を受け付けて、各パスについて以下を実施する
指定レイアウトである左右分割状態でセッション 'path_to_dir' を開始する
左右それぞれで 'nix develop' コマンドが実行される

"
def tmuxInWindow := "
目的は以下のmain処理をもつshファイルを作成することである
shebangでnix shell起動、nixpkgs#tmuxを環境に用意する
main処理は指定リポジトリパス配列を受け付ける、リポジトリパスはローカルの場合ディレクトリパスである
main処理は上記を受け付けて、各パスについて以下を実施する
指定レイアウトである左右分割状態でセッション 'path_to_dir' を開始する
左ペインには2ウィンドウ[bash, bash]の別セッション 'path_to_dir_bb' を開始してアタッチする
右ペインには3ウィンドウ[hx, lazygit, yazi] 'path_to_dir_hly' を開始してアタッチする

結果指定ディレクトリのセッションは、指定ディレクトリの左右セッションをatattchした状態で見えている状態になっているはずである
"

def task2503110900 := "
目的：
cloudbuild.run.yamlの設定が、GCSバケット上のファイルから環境変数を取得してDockerfileに適用するよう改善されること

背景：
Dockerfileは env.sh ファイルを必要としている
この必要なファイルをGCP内部で提供できる状態になっていない

ユーザーが検討した手順：
cloudbuild.run.yamlでGCSのファイルを取得設定可能であり
cloudbuild.run.yamlのstepで使用しているDockerfileがそれを読み取れるなら
それを設定したい
もし不可能である場合はこのタスクを中断すること

可能な場合
ユーザーにバケットへenv.shファイルをアップロードするTODOをタスクファイルへ追加してほしい
またデバッグ処理としてenv.shファイルを読み取れたことが可能なlogをGCLに残してほしい
すでにGCLにはCloudBuildに関するログが残るようになっている
もし不可能である場合はこのタスクを中断すること

バケット名などの保存先情報に関してはenv.shを読み取ってよいのでハードコーディングで設定してほしい
もし不可能である場合はこのタスクを中断すること

ユーザーnixosは設定されたバケットのルートに env.sh を格納完了した
またローカルのenv.shファイルを_env.shファイルに命名変更したので、cloudbuild.run.yamlが正確な記述なら次のコマンドでgcsバケットのenv.shファイルを読み取りビルドを成功させられると思っている `gcloud builds submit --config cloudbuild.run.yaml`
もし誤りがある場合は指摘すること

以上
なお、ユーザーが検討した手順には不具合がある可能性があるので、もし存在する場合は最初に指摘すること
"

def task2503111000 := "
目的：
cloudbuild.function.yamlの設定が、GCSバケット上のファイルから環境変数env.yamlを取得して適用するよう改善されること

背景：
この必要なファイルをGCP内部で提供できる状態になっていない

ユーザーが検討した手順：
cloudbuild.function.yamlでGCSのファイルを取得設定可能であるなら それを設定したい
ユーザーnixosは設定されたバケットルート配下の/configに、 env.yaml を格納完了した
またローカルのenv.yamlファイルを_env.yamlファイルに命名変更したので、cloudbuild.function.yamlが正確な記述なら次のコマンドでgcsバケットのenv.yamlファイルを読み取りビルドを成功させられると思っている `gcloud builds submit --config cloudbuild.function.yaml`
もし誤りがある場合は指摘すること
もし不可能である場合はこのタスクを中断すること

可能な場合
またデバッグ処理としてenv.yamlファイルを読み取れたことが可能なlogをGCLに残してほしい
すでにGCLにはCloudBuildに関するログが残るようになっている
もし不可能である場合はこのタスクを中断すること

バケット名などの保存先情報に関しては_env.shを読み取ってよいのでハードコーディングで設定してほしい
もし不可能である場合はこのタスクを中断すること


以上
なお、ユーザーが検討した手順には不具合がある可能性があるので、もし存在する場合は最初に指摘すること
"

def task2503111130 :="
教えてほしい
セッションネストの必要ある？
ディレクトリ変更が一つのセッションであるのはよいのでは→ディレクトリに戻ったときに自動的にセッションにアタッチすればよいように
さらに各ディレクトリの中でセッションを立ち上げたい、leftセッションとrightセッション
"

-- def convention := "

-- -- '
-- -- ### 基本概念

-- -- - **TDD基本概念**: `rules/tdd.md` で詳細に説明されています。
-- --     - Red-Green-Refactor サイクル
-- --     - テストは仕様である
-- --     - Assert-Act-Arrange の順序（ただし考える順序は Assert -> Act -> Arrange）
-- -- - **コーディング原則 (FP, DDD, TDD)**: `rules/coding.md` で説明されています。
-- --     - 関数型アプローチ (FP)
-- --         - 純粋関数を優先
-- --         - 不変データ構造
-- --         - 副作用の分離
-- --         - 型安全性の確保
-- --     - ドメイン駆動設計 (DDD)
-- --         - 値オブジェクトとエンティティの区別
-- --         - 集約による整合性保証
-- --         - リポジトリによるデータアクセス抽象化
-- --         - 境界付けられたコンテキスト
-- --     - テスト駆動開発 (TDD): 上記の「TDD基本概念」に同じ

-- -- ### モード

-- -- - **各種モード (Script, TDD, Module, LibraryResearcher, mizchi:writer)**: 各 `roomodes/*.md` ファイルで詳細が定義されています。
-- --     - **Script モード**: `roomodes/deno-script.md`
-- --         - 単一ファイル完結型
-- --         - テストコードも同一ファイル内
-- --         - `@script` ディレクティブまたは `scripts/*`, `script/*`, `poc/*` 配下
-- --         - 外部依存を最小限に
-- --     - **TDD モード**: `roomodes/deno-tdd.md`
-- --         - テスト駆動開発を実践するモード
-- --         - `@tdd` ディレクティブ
-- --         - テストファースト
-- --         - テストは仕様
-- --         - テスト実装順序 (Assert -> Act -> Arrange)
-- --         - リファクタリングフェーズの重要性 (静的解析、デッドコード削除、カバレッジ測定、Git連携)
-- --         - TypeFirst モード (型定義を先行)
-- --     - **Module モード**: `roomodes/deno-module.md`
-- --         - 複数ファイルで構成されるモジュール開発
-- --         - ディレクトリ構造 (`modules/<name>/`)
-- --         - `mod.ts`, `deps.ts`, `lib.ts`, `types.ts`, `*.test.ts` の役割
-- --         - `mod.ts` と `deps.ts` によるコンテキスト定義
-- --         - モジュール読み方 (README.md, deno doc, テストケース)
-- --         - テストが落ちた時の手順
-- --     - **LibraryResearcher モード**: `roomodes/library-searcher.md`
-- --         - ライブラリ調査・チートシート作成モード
-- --         - `docs/libraries/` 以下にドキュメント作成
-- --         - チートシート形式 (機能一覧、サンプルコード、概念と型対応)
-- --         - `searchWeb`, `searchNpm`, `deno run -A jsr:@mizchi/npm-summary/cli pkgname`, `deno doc jsr:*` などのMCPツール/コマンド活用
-- --         - 既存ドキュメントがある場合の対応
-- --         - ライブラリ名不明な場合の検索
-- --     - **mizchi:writer モード**: `roomodes/mizchi-writer.md`
-- --         - mizchi (ユーザー) の文体・技術的特徴を模倣した記事作成モード
-- --         - mizchi の技術的専門性、文体、記事構成、表現、記事構成パターン、AI技術への洞察、教育的アプローチなどを詳細に分析
-- --         - 記事作成時の指針 (結論先出し、段階的説明、コード例重視、実践的価値提供)

-- -- ### 開発ワークフロー

-- -- - **TDD開発手順**: `roomodes/deno-tdd.md`, `rules/tdd.md` に記載。
-- --     - Red: 失敗するテストを書く
-- --     - Green: テストを通る最小限の実装
-- --     - Refactor: コード改善
-- --     - Deno における TDD 手順 (ディレクトリ構成、テスト作成、テスト失敗確認、実装、テスト成功確認)
-- --     - 落ちるテスト追加手順 (テスト成功確認 -> 落ちるテスト追加 -> テスト失敗確認 -> 落ちたテストのみ再実行 -> 型定義 -> 実装)
-- -- - **テスト追加手順**: `roomodes/deno-tdd.md` の「落ちるテストを追加するときの手順」に詳細。
-- --     - テスト成功確認 -> 落ちるテスト追加 -> テスト失敗確認 -> 落ちたテストのみ再実行 -> 型定義 -> 実装
-- -- - **リファクタリング手順**: `roomodes/deno-tdd.md`, `rules/tdd.md` に記載。
-- --     - テスト成功後に行う
-- --     - `deno check`, `deno lint` による静的解析
-- --     - TSR によるデッドコード削除
-- --     - コードカバレッジ測定 (`deno test --coverage`, `deno coverage`)
-- -- - **Gitワークフロー**: `rules/_git.md`, `roomodes/deno-tdd.md` (TDDにおけるGit連携) に記載。
-- --     - コミット作成手順 (変更確認 -> 分析 -> メッセージ作成 -> 実行)
-- --     - プルリクエスト作成手順 (ブランチ状態確認 -> 分析 -> 作成)
-- --     - コミットメッセージ、プルリクエストの例
-- --     - TDD 各フェーズ (テスト修正後、実装後、リファクタリング後) のコミット推奨
-- -- - **モジュール開発手順**: `roomodes/deno-module.md` の「モジュールモード」の説明が該当。
-- --     - ディレクトリ作成 (`modules/<name>/`)
-- --     - ファイル作成 (`mod.ts`, `deps.ts`, `lib.ts` など)
-- --     - `mod.ts` でのエクスポート、`deps.ts` での依存管理
-- --     - 実装は `lib.ts` 以下
-- --     - テストは `*.test.ts`
-- -- - **メモリバンク更新ワークフロー**: `rules/_memory.md` の「ドキュメントの更新」に記載。
-- --     - 新しいプロジェクトパターンの発見時
-- --     - 重要な変更実装後
-- --     - ユーザーが `update memory` を要求した場合
-- --     - コンテキスト明確化が必要な場合
-- --     - 更新プロセス (全ファイルレビュー -> 現状ドキュメント化 -> 次のステップ明確化 -> `.clinerules` 更新)

-- -- ### コーディングルール

-- -- - **Denoルール**: `rules/deno.md` に記載。
-- --     - npm 互換モード (`npm:`, Node.js API 利用可能)
-- --     - 外部ライブラリ使用方法 (`jsr:`, `npm:`, `https://deno.land/x/`)、推奨ライブラリ (`jsr:@david/dax`, `@std/expect`, `@std/testing`)
-- --     - `deno doc`, `npm-summary` でのライブラリ情報確認
-- --     - `deno add` での依存関係追加
-- --     - `deno doc ../foo/mod.ts` での型定義確認
-- --     - テスト (`@std/expect`, `@std/testing/bdd` 使用、`describe` 不要)
-- --     - アサーション (`expect(result, "<expected behavior>").toBe("result")`)
-- --     - モジュール間の依存関係ルール (`mod.ts` 経由、直接参照禁止、同一モジュール内は相対パス、`deps.ts` 参照)
-- --     - 依存関係検証 (`deno task check:deps`, `deno lint` の mod-import ルール)
-- --     - コード品質監視 (カバレッジ: `deno task test:cov`, デッドコード解析: TSR)
-- --     - 型定義による仕様抽出 (dts)
-- -- - **TypeScriptルール**: `rules/typescript.md` に記載。
-- --     - 方針 (型ファースト、仕様コメント、関数優先、アダプターパターン)
-- --     - 型の使用方針 (具体的な型、`any` 回避、`unknown` から絞り込み、Utility Types 活用、型エイリアス命名)
-- --     - エラー処理 (Result型 `npm:neverthrow` 使用、エラー型定義)
-- --     - 実装パターン (関数ベース、classベース、Adapterパターン、選択基準)
-- --     - 一般的なルール (依存性注入、インターフェース設計、テスト容易性、コード分割)
-- -- - **モジュールルール**: `roomodes/deno-module.md`, `rules/deno.md` のモジュール関連記述を参照。
-- --     - モジュール構造 (`modules/<name>/mod.ts`, `deps.ts`, `lib.ts` など)
-- --     - `mod.ts` は re-export のみ、実装を含まない
-- --     - `deps.ts` で依存関係一元管理
-- --     - モジュール間の参照は `mod.ts` 経由
-- --     - モジュール参照時は `jsr:` や `npm:` 非推奨、`deno add` で `deno.json` に依存追加
-- -- - **テストルール**: `rules/deno.md`, `roomodes/deno-tdd.md`, `rules/tdd.md` に記載。
-- --     - テストフレームワーク (`@std/testing/bdd`)、アサーションライブラリ (`@std/expect`)
-- --     - `describe` による入れ子不要
-- --     - アサーション記述 (`expect(result, "<expected behavior>").toBe("result")`)
-- --     - テスト実装順序 (Assert -> Act -> Arrange)
-- --     - テスト名形式: 「{状況}の場合に{操作}をすると{結果}になること」
-- -- - **エラー処理ルール**: `rules/typescript.md` のエラー処理セクションに記載。
-- --     - Result型 (`npm:neverthrow`) の使用
-- --     - エラー型の定義 (具体的なケース列挙、エラーメッセージ)
-- -- - **実装パターン**: `rules/typescript.md`, `rules/coding.md` に記載。
-- --     - 関数ベース vs classベース (選択基準あり)
-- --     - Adapterパターン (外部依存抽象化)
-- --     - 値オブジェクト、エンティティ (DDD原則)
-- --     - Result型
-- -- - **コードスタイル**: `rules/coding.md`, `rules/typescript.md` に記載。
-- --     - 関数優先 (class は必要な場合のみ)
-- --     - 不変更新パターン
-- --     - 早期リターン
-- --     - エラーとユースケースの列挙型定義

-- -- ### ファイル構造

-- -- - **ディレクトリ構造**: `rules/directory-patterns.md`, `roomodes/deno-module.md`, `rules/_memory.md` に記載。
-- --     - 基本構造: `.cline/`, `docs/`, `apps/`, `modules/`, `poc/`, `tools/`
-- --     - `.cline/`: プロンプト関連ファイル (`build.ts`, `roomodes/`, `rules/`)
-- --     - `docs/`: ドキュメント (`libraries/` 以下にライブラリチートシート)
-- --     - `apps/`: アプリケーション
-- --     - `modules/`: Deno モジュール (`modules/<name>/mod.ts` など)
-- --     - `poc/`: PoC (単体実行可能スクリプト)
-- --     - `tools/`: PoC 用ユーティリティ
-- --     - メモリバンク: `.cline/memory/*` (`projectbrief.md`, `productContext.md` など)
-- -- - **モジュールファイル構造**: `roomodes/deno-module.md` の「Module」セクションに詳細。
-- --     - `modules/<name>/`
-- --         - `mod.ts`: 外部向けエクスポート (re-export のみ)
-- --         - `deps.ts`: 依存関係定義 (モジュール内 re-export)
-- --         - `lib.ts`: 実装 (deps.ts から import)
-- --         - `types.ts`: 型定義
-- --         - `lib.test.ts`, `test/*.test.ts`: テストコード
-- -- - **メモリバンクファイル構造**: `rules/_memory.md` の「メモリバンクの構造」セクションに詳細。
-- --     - `.cline/memory/*`
-- --     - コアファイル (必須):
-- --         - `projectbrief.md`: プロジェクト概要、コア要件・目標
-- --         - `productContext.md`: プロジェクトの存在理由、解決問題、ユーザー体験目標
-- --         - `activeContext.md`: 現在の作業焦点、最近の変更、次のステップ、決定事項
-- --         - `systemPatterns.md`: システムアーキテクチャ、技術的決定、設計パターン、コンポーネント関係
-- --         - `techContext.md`: 使用技術、開発環境、技術制約、依存関係
-- --         - `progress.md`: 機能している部分、未構築部分、現状、既知の問題
-- --     - 追加コンテキスト (任意): 複雑な機能ドキュメント、統合仕様、APIドキュメント、テスト戦略、デプロイ手順など

-- -- ### その他

-- -- - **人格・口調 (ずんだもん)**: `rules/zunda.md` に詳細。
-- --     - 一人称: 「ぼく」
-- --     - 文末: 「〜のだ。」「〜なのだ。」 (疑問文: 「〜のだ？」)
-- --     - 使わない口調: 「〜なのだよ。」「〜なのだぞ。」「〜なのだね。」「のだね。」「のだよ。」
-- -- - **メモリバンク**: `rules/_memory.md` に詳細。
-- --     - セッション間で記憶リセット
-- --     - メモリバンクへの依存 (開始時に全ファイル読み込み必須)
-- --     - 構造 (コアファイル + 追加コンテキスト、Markdown形式、`.cline/memory/*` 配下)
-- --     - コアワークフロー (計画モード、実行モード)
-- --     - ドキュメント更新タイミングと手順
-- --     - 記憶量制限、ファイルサイズ確認 (`ls -al`)
-- --     - 会話継続時の memorybank 更新提案
-- -- - **プロジェクトインテリジェンス (.clinerules)**: `rules/_memory.md`, `build.ts` に記載。
-- --     - プロジェクト学習ジャーナル (`rules/_memory.md`)
-- --     - コードから不明なパターン、設定、洞察を記録
-- --     - 記録内容例 (実装パス、ユーザー好み、プロジェクト固有パターン、課題、決定事項、ツール使用パターン)
-- --     - 形式は柔軟 (`rules/_memory.md`)
-- --     - `.clinerules` 生成スクリプト (`build.ts`)
-- -- - **Git 注意事項**: `rules/_git.md`, `rules/00_basic.md` に記載。
-- --     - コミット関連 (可能な限り `git commit -am`、関係ないファイル含めない、空コミットNG、git設定変更NG)
-- --     - プルリクエスト関連 (必要に応じてブランチ作成、適切にコミット、`-u` フラグでpush、全変更分析)
-- --     - 避けるべき操作 (対話的 git コマンド、リモートリポジトリへ直接push、git設定変更)
-- --     - `rules/00_basic.md`: 作業開始前に `git status` 確認、無関係な変更が多い場合は別タスク提案
-- -- - **作業開始準備**: `rules/00_basic.md`, `rules/_git.md` に記載。
-- --     - `rules/00_basic.md`: `git status` で git コンテキスト確認、無関係な変更が多い場合は別タスク提案
-- --     - `rules/_git.md`: 「コミットの作成」の「1. 変更の確認」を参照

-- -- '
-- -- {args}!
-- -- "
-- "

def predict := ""
-- TODO 例からフォーマットされた例で抽象化する
-- def formatAbstractingExample := predict example
-- TODO mermaid mcpが出てきそう
def explainCodeMermaid := "
以下の処理の流れをmermaidのTDフローチャート図示したい 
ノードの粒度は「処理概要」だけとすること
分岐がある場合はダイヤモンドとすること、異常終了がある各ノード自身が分岐ノードとなることになることを理解すること
色付けはしないこと

無事Mermaid記法が生成された際
その記法にエラーがないか3回繰り返して確認すること

すべてのノード名は””で囲むこと

特に以下と同様のエラーが発生しないように抽象的に理解することで注意すること
Expecting 'SQE', 'DOUBLECIRCLEEND', 'PE', '-)', 'STADIUMEND', 'SUBROUTINEEND', 'PIPE', 'CYLINDEREND', 'DIAMOND_STOP', 'TAGEND', 'TRAPEND', 'INVTRAPEND', 'UNICODE_TEXT', 'TEXT', 'TAGSTART', got 'PS'
　
Expecting 'SEMI', 'NEWLINE', 'SPACE', 'EOF', 'SHAPE_DATA', 'STYLE_SEPARATOR', 'START_LINK', 'LINK', got 'PS'

では生成してください



 処理ステップ一覧 
 IP一覧取得処理 

 項目  説明 
 処理概要    AIコメント作成対象のIPをBigQueryから取得する 
 〇〇処理    BigQueryに対してクエリを実行し、AIコメント作成の対象となるIPのリストを取得する。 抽出条件として、Xのメンション数と対前日上昇率を用いる。 具体的には、Xのメンション数が40001以上かつ対前日上昇率0%以上、またはXのメンション数が10000以上かつ対前日上昇率150%以上を満たすIPを対象とする。 TODO: 実際のSQLクエリの内容をTODOとして残す。可能であれば analyze_target.execute_query の実装を確認し、クエリ内容を仕様書に反映すること。 
 引数  BigQueryクライアント 
 環境変数    なし 
 異常終了    BigQueryError をログ出力 
 リトライ戦略  TODO: リトライ戦略が不明 
 トランザクション制御  なし 

 データフレームフィルタリング処理 

 項目  説明 
 処理概要    取得したIPリストをデータフレーム形式でフィルタリング 
 〇〇処理    BigQueryから取得したIPリスト（pd.DataFrame形式）に対して、SQL側で実施すると複雑になるフィルタリング処理を適用する。 具体的には、以下の条件でフィルタリングを行う。 - document_cnt_rate_of_inc が0より大きい - document_cnt_sum が moving_avg_90_percentile より大きい - document_cnt_sum が 10000 以上 
 引数  IPリスト (pd.DataFrame) 
 環境変数    なし 
 異常終了    なし 
 リトライ戦略  なし 
 トランザクション制御  なし 

 AIコメント生成処理 

 項目  説明 
 処理概要    フィルタリングされたIPに対してAIコメントを生成 
 〇〇処理    フィルタリング処理を通過したIPリストに含まれる各IPに対して、AIコメントを生成する。 AIコメント生成には AICommentBuilder クラスの main メソッドを使用する。 生成されたAIコメントは、IP ID、キーワード、URL、集計日、タイトル、コメント、作成日時などの情報を含むデータ形式 (Analyzed 型) で取得される。 
 引数  フィルタリング済みIPリスト (pd.DataFrame) 
 環境変数    RETRY_COUNT (リトライ回数), WEB_SITE_SEARCH_DAYS_BEFORE (Webサイト検索期間(前)), WEB_SITE_SEARCH_DAYS_AFTER (Webサイト検索期間(後)) TODO: WEB_SITE_SEARCH_DAYS_BEFORE, WEB_SITE_SEARCH_DAYS_AFTER が環境変数として外部から設定されるものか、設定ファイルで定義された定数か確認し、仕様書を修正すること。 
 異常終了    SearchError, VertexAiError をログ出力 
 リトライ戦略  最大リトライ回数 RETRY_COUNT 
 トランザクション制御  なし 

 構造データ格納処理 

 項目  説明 
 処理概要    生成されたAIコメントをCloud StorageにParquet形式で格納 
 〇〇処理    生成されたAIコメントデータ (ai_comments) を、指定された Cloud Storage バケット (CLOUD_STORAGE_BUCKET_NAME) 内に、日付 (file_date) をファイル名に含む Parquet 形式ファイルとして格納する。 格納処理には store.analyzed_results 関数を使用する。 
 引数  AIコメントデータ (Analyzedのリスト), Cloud Storageクライアント, バケット名, ファイル名 
 環境変数    CLOUD_STORAGE_BUCKET_NAME (Cloud Storage バケット名) 
 異常終了    StorageError をログ出力 
 リトライ戦略  TODO: リトライ戦略が不明 
 トランザクション制御  なし 

 処理完了通知処理 

 項目  説明 
 処理概要    バッチ処理の完了をSlack通知 
 〇〇処理    バッチ処理が正常に完了したことをSlackに通知する。 通知には notify.send_success 関数を使用し、メッセージとして 'ジョブ実行は成功しました！' を送信する。 
 引数  Slackクライアント 
 環境変数    なし 
 異常終了    WebhookError をログ出力 
 リトライ戦略  TODO: リトライ戦略が不明 
 トランザクション制御  なし 

 ログ出力処理 (正常終了) 

 項目  説明 
 処理概要    正常終了時のログ出力 
 〇〇処理    処理が正常に終了した場合、ログに正常終了メッセージと処理コード 0 を出力する。 
 引数  ログ出力処理 
 環境変数    なし 
 異常終了    なし 
 リトライ戦略  なし 
 トランザクション制御  なし 

 ログ出力処理 (異常終了) 

 項目  説明 
 処理概要    異常終了時のログ出力 
 〇〇処理    処理が異常終了した場合、エラーログとエラー情報をログに出力する。 Slack通知 (notify.send_error) を実行し、エラーメッセージとメンション対象メンバー (NOTIFICATION_MENTION_MEMBERS) を通知する。 発生した例外の種類に応じて、対応するエラーログ（WebhookError, BigQueryError, VertexAiError, SearchError, SecretError, StorageError, VariablesError, Exception）を出力する。 
 引数  エラー情報, ログ出力処理, Slackクライアント 
 環境変数    NOTIFICATION_MENTION_MEMBERS (Slack通知メンション対象), Features.ANALYZE.value (機能名) 
 異常終了    なし 
 リトライ戦略  なし 
 トランザクション制御  なし 

 接続終了処理 

 項目  説明 
 処理概要    各種接続の終了処理 
 〇〇処理    処理の最後に、必要となる各種接続を終了する。 
 引数  BigQuery クライアント, その他接続 (TODO: 接続の種類を特定, analyze_target.execute_query の finally句での実行意図も不明) 
 環境変数    なし 
 異常終了    なし 
 リトライ戦略  なし 
 トランザクション制御  なし 

 TODO 
 IP一覧取得処理 - 〇〇処理: 実際のSQLクエリの内容をTODOとして残す。可能であれば analyze_target.execute_query の実装を確認し、クエリ内容を仕様書に反映すること。 
 AIコメント生成処理 - 環境変数: WEB_SITE_SEARCH_DAYS_BEFORE, WEB_SITE_SEARCH_DAYS_AFTER が環境変数として外部から設定されるものか、設定ファイルで定義された定数か確認し、仕様書を修正すること。 
 リトライ戦略: IP一覧取得処理、構造データ格納処理、処理完了通知処理におけるリトライ戦略がコードから不明のため、TODOとして残しました。 
 接続終了処理 - 引数: analyze_target.execute_query の finally句での実行意図、および接続終了処理の内容をTODOとして残す。実装を確認し、接続終了処理の内容と引数を特定すること。 
 修正点まとめ 

 IP一覧取得処理 - 〇〇処理: TODO追記 (SQLクエリ内容) 
 データフレームフィルタリング処理 - 〇〇処理: 条件を修正 (document_cnt_sum が 10000 以上) 
 AIコメント生成処理 - 環境変数: TODO追記 (WEB_SITE_SEARCH_DAYS_BEFORE, WEB_SITE_SEARCH_DAYS_AFTER の定義元確認) 
 接続終了処理 - 引数: TODO追記 (analyze_target.execute_query finally句の意図、接続の種類) 
 上記修正版仕様書をご確認いただき、問題ないようでしたら、完了とさせていただきます。 
 引き続き、レビューをお願いいたします。修正版仕様書を確認しました。 
 迅速な修正と詳細なTODOの追記、ありがとうございます。 

 修正点、確認点として指摘させていただいた事項は、全て修正版仕様書に反映されており、 
 内容も適切であると判断いたしました。 

 特に、以下の点について、改善されていることを確認しました。 

 IP一覧取得処理 - 〇〇処理: SQLクエリの内容をTODOとして追記 
 データフレームフィルタリング処理 - 〇〇処理: フィルタリング条件の修正 (document_cnt_sum が 10000 以上) 
 AIコメント生成処理 - 環境変数: 環境変数の定義元に関するTODO追記 
 接続終了処理 - 引数: analyze_target.execute_query finally句の意図不明点をTODO追記

"

def code := ""
-- 
-- TODO コード説明
-- def explainCode := predict(prompt([]))

def promptForFormat := "
目的は以下のフォーマットに従って, codeのための仕様書を生成することである

なおcode2はcode1の一部で利用されているため、生成された仕様書は与えられたcodeすべての構造を理解している必要があるため、上記目的を達成するにあたり注意すること

また仮に意図が不明なcodeや、フォーマットに従って仕様書を生成するにあたりフォーマットが不明確な場合は、生成された仕様書内にTODOとして残すことでのみ対応し、いったん仕様書を完成させること

では完成された仕様書を見せてほしい







フォーマット＝＝＝

処理フォーマット（抽象化）

本処理は、複数のステップから構成され、各ステップは以下の共通フォーマットに従うものとする。



共通フォーマット

処理概要 (処理の目的・内容)

〇〇処理：具体的な処理内容を記述 (具体的な処理の目的や内容を簡潔に記述)

引数 (入力)

各処理に必要な引数を列挙 (処理ステップへの入力となる引数を列挙)例：〇〇クライアント, 〇〇データ, 〇〇クエリ

環境変数 (設定)

各処理に必要な環境変数を列挙 (処理ステップの動作を設定する環境変数を列挙)例：〇〇_ID, 〇〇_KEY, MAX_RETRIES

異常終了 (エラーハンドリング)

異常終了時の動作を記述 (処理ステップでエラーが発生した場合の動作を記述)ログ出力：〇〇Error をログ出力

リトライ戦略：指数バックオフ、最大リトライ回数 MAX_RETRIES

トランザクション制御：必要に応じてトランザクションロールバック (rollback_transaction())

処理ステップ一覧 (例)

IP一覧取得処理

Web記事データ取得処理

関連記事抽出生成処理

コメント付加構造データ生成処理

構造データ格納処理

処理完了通知処理

共通処理 (終了処理)

接続終了処理 (各種接続の終了処理)

ログ出力処理 (ログ出力に関する共通処理)正常終了ログ出力：処理コード 0 の場合

異常終了ログ出力：処理コード 0 以外の場合

フォーマットサンプル使用手順書

この手順書は、インプットコードから処理フォーマット（抽象化）されたアウトプットサンプルを生成するためのものです。

手順:



インプットコードを理解する:

インプットコード（例：Pythonコード）全体を読み、コードの目的、全体的な機能、処理の流れを把握します。

各処理ステップ間のデータの流れ、主要な関数、外部サービスとの連携などを理解します。

処理ステップを特定する:

インプットコードを論理的な処理ステップに分割します。 コード内の関数呼び出し、主要な処理ブロック、処理フェーズなどを区切りとして考えます。

例：IPアドレスの取得、Web記事のデータ取得、AIコメントの生成、データ格納、通知送信など。

各処理ステップに対して「共通フォーマット」の各項目を記述する:

各処理ステップについて、以下の情報を記述します。処理概要 (処理の目的・内容): その処理ステップが何をするのかを、簡潔かつ抽象的に記述します。 処理の具体的な実装方法ではなく、目的や内容を記述します。

引数 (入力): その処理ステップへの入力となる引数を列挙します。 関数への引数、前のステップからのデータ、ステップ内で使用されるデータなどを考えます。 具体的な変数名ではなく、引数の種類（例：BigQueryクライアント、クエリ、データなど）を記述します。

環境変数 (設定): その処理ステップで使用される環境変数を列挙します。 環境変数は通常、設定値としてコード外から渡されるものです。 環境変数名をリストアップします。

異常終了 (エラーハンドリング): その処理ステップでエラーが発生した場合の動作を記述します。 ログ出力、エラー処理、リトライ戦略、トランザクションロールバックなどを考慮し、コードのエラーハンドリング部分を参照して記述します。

「共通処理」を特定し記述する:

コード全体を通して、処理の最後に必ず実行される共通的な処理（例：接続の終了、ログ出力など）を特定します。 'finally' ブロックや、終了時に呼び出される関数などを探します。

「接続終了処理」、「ログ出力処理（正常終了・異常終了）」などの共通処理を記述し、それぞれの引数についても記述します。

アウトプットサンプルを組み立てる:

手順3と4で収集した情報を、提供されたアウトプットサンプルの形式でまとめます。

各処理ステップ、共通処理を見出しとして、その下に「共通フォーマット」で記述した内容を配置します。

アウトプットサンプルを参考に、適切な見出し、フォーマット、インデントなどを用いて、情報を整理し、読みやすいドキュメントを作成します。

手順とフォーマットサンプルのレビューと改善:

作成した手順書を用いて、別のインプットコードからアウトプットサンプルを生成してみます。

生成されたアウトプットサンプルが期待通りであるか、手順書は分かりやすいか、フォーマットサンプルは適切かなどを検証します。

必要に応じて、手順書、フォーマットサンプルを修正し、より正確で汎用的なものに改善します。

"

def targetCode : String :=
```
def reanalyze(ip_id: str, ip_name: str, aggregate_date: str) -> None:
    logging.info(''.center(80, '='))

    ai_comment_builder = create_comment.AICommentBuilder()
    reanalyzed_comment: Analyzed = ai_comment_builder.main(
        ip_id,
        ip_name,
        aggregate_date
    )

    logging.info(''.center(80, '='))

    store.reanalyzed_results(
        [reanalyzed_comment],
        variables.CLOUD_STORAGE_BUCKET_NAME,
        file_name.parquet_for_reanalyzed(
            get_datetime.date_for_filename(aggregate_date)
        )
    )
class AICommentBuilder:
    def __init__(
        self
    ) -> None:
        self.llm = create_llm_answer.LLM()

    def exclude_not_related_article(
        self, 
        ip_name: str, 
        search_bing_data: list
    ) -> list:

        related_articles = []
        for article in search_bing_data['webPages']['value']:
            # if ip_name in article['name'] or ip_name in article['snippet']:
            #     related_articles.append(article)

            # GCP移行後の仕様変更により、フィルタリング処理の除外（器のみ残し）
            related_articles.append(article)
        
        return related_articles


    def main(
        self, 
        ip_id: str, 
        ip_name: str, 
        aggregate_dt: str,
        # document_cnt: int, 
    ) -> None | Analyzed:
        # 既に対象の「ip_id」、「aggregate_date」のコメントが存在しないかチェック
        # WARNING 現在常にFalseを返却する
        if dbg.check_already_exists_item(ip_id, aggregate_dt):
            logging.debug(f'{ip_id} is already exists in database.')
            return

        # AIコメントデータ作成
        for _ in range(variables.RETRY_COUNT):
            try:
                # IP名で検索
                keyword = f'' + urllib.parse.quote(ip_name).replace('-', '%22')

                logging.debug(f'keyword: {keyword}')
                logging.debug(f'aggregate_dt: {aggregate_dt}')
                # logging.debug(f'document_cnt: {document_cnt}')

                # 記事検索期間を指定する
                web_search_range_from = datetime.strftime(datetime.strptime(aggregate_dt, '%Y-%m-%d') - timedelta(days=variables.WEB_SITE_SEARCH_DAYS_BEFORE), '%Y-%m-%d')
                web_search_range_to = datetime.strftime(datetime.strptime(aggregate_dt, '%Y-%m-%d') + timedelta(days=variables.WEB_SITE_SEARCH_DAYS_AFTER), '%Y-%m-%d')

                # Bingからデータを取得する
                search_bing_data = bing_search.get_bing_data(keyword, 10, web_search_range_from, web_search_range_to)
                logging.debug("search_bing_data")
                logging.debug(search_bing_data)

                # 「記事タイトル」もしくは「記事スニペット」にアニメ名（keyword）が含まれていなかったら、その記事は除外
                related_articles = self.exclude_not_related_article(ip_name, search_bing_data)
                logging.debug('関連記事数： {}'.format(len(related_articles)))

                if len(related_articles) >= 3:
                    # LLMに見解コメント作成してもらう（json形式想定）
                    llm_answer_dict: PredictedItem = self.llm.create_comments_about_a_keyphrase(keyword, related_articles, web_search_range_from, web_search_range_to)
                else:
                    llm_answer_dict = {}
                    for i, article in enumerate(related_articles, start=1):
                        llm_answer_dict[str(i)] = {
                            'article_num': str(i), 
                            'title': article['name'], 
                            'url': article['url'], 
                            'comment': article['snippet']
                        }

                logging.debug('llm_answer_dict')
                logging.debug(f"{llm_answer_dict}")

                # AIの見解コメント（3記事分に対する）を1つに要約させる
                if len(related_articles) != 0:
                    llm_answer_summary: str = self.llm.summary_comment(llm_answer_dict)
                else:
                    llm_answer_summary = '関連する記事がありませんでした。'

                # 「,」を「%d」にエスケープ（AIコメント）
                llm_answer_summary = llm_answer_summary.replace('%', '%c').replace(',', '%d')

                # タイトル成形
                title_list = [
                    llm_answer_dict[k]['title'].replace('%', '%c').replace(',', '%d')
                    for k in llm_answer_dict.keys()
                ]
                while len(title_list) < 3:
                    title_list.append('キーワードに該当する作品タイトルはありませんでした。')
                title = ','.join(title_list)
                # title = ','.join([
                #     llm_answer_dict[k]['title'].replace('%', '%c').replace(',', '%d')
                #     for k in llm_answer_dict.keys()
                # ])

                # url成形
                # LLMが参照した記事番号を使用して、記事生データからURLを取得する。
                url_list = []
                for k in llm_answer_dict.keys():
                    article_index = int(llm_answer_dict[k]['article_num']) - 1
                    url_list.append(related_articles[article_index]['url'])

                    # url = llm_answer_dict[k]['url']
                    # if url.find('sample.com') != -1:
                    #     # ハルシネーションにより、ダミーのURLが含まれている場合
                    #     logging.debug('ハルシネーション発生。')
                    #     logging.debug(f'url: {url}')

                    #     try:
                    #         article_index = int(llm_answer_dict[k]['article_num']) - 1
                    #         url_list.append(search_bing_data['webPages']['value'][article_index]['url'])
                    #     except:
                    #         url_list.append(url)
                    #     finally:
                    #         continue
                while len(url_list) < 3:
                    url_list.append('')
                url = ','.join(url_list)


                comment_data: Analyzed = {
                    'ip_id': ip_id, 
                    'keyword': ip_name, 
                    # 'count': document_cnt,
                    'url': url, 
                    'aggregate_date': aggregate_dt, 
                    'title': title, 
                    'comment': llm_answer_summary, 
                    'created_at': get_datetime.now_formatted()
                }

                return comment_data
            except:
                e = sys.exc_info()[1]
                if _ == variables.RETRY_COUNT - 1:
                    if isinstance(e, SearchError):
                        raise SearchError(f"{e}")
                    else:
                        raise VertexAiError(f"{e}")
                else:
                    logging.info('Retry.')
 
"""


def main : IO Unit := do
-- def main (args : List String) : IO Unit := do
  let name ← IO.getEnv "USER"
  match name with
  | some username => IO.println s!"{username}
{promptForFormat}
{targetCode}
"
  | none => IO.println "wait..."

