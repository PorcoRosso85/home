{
  description = "Flake依存関係の解析と構造化ドキュメントシステム";
  goal = [
    "readme.nixによるディレクトリ責務の構造化定義"
    "flake依存関係のJSON形式でのインデクス化"
    "collectDocsによる全readme.nixの自動収集"
    "depsIndexによる依存flakeの構成要素把握"
  ];
  nonGoal = [
    "実装コードの生成や変更"
    "外部サービスとの連携"
    "GUIツールの提供"
  ];
}