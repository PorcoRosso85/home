{
  description = "共通ヘッダ付与・冪等WAL→R2耐久・監査バンドル出力の基盤";

  goal = [
    "event-header: ID/時刻/種別/相関IDの付与と正規化"
    "durable-log: 冪等WAL→R2（原本保全）"
    "audit-trail: Correlationで来歴を束ねてエクスポート"
  ];

  nonGoal = [
    "業務判定/通知/重い集計/可視化"
  ];

  meta = {
    owner = [ "@you" ];
    lifecycle = "experimental";
  };

  output = {
    packages = [ ];
    apps = [ ];
    modules = [ ];
    overlays = [ ];
    devShells = [ ];
  };
}