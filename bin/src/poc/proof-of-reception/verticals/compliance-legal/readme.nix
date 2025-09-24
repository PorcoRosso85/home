{
  description = "規制/開示の監視→耐久→監査再現を最短の価値線で提供";

  goal = [
    "monitor: ソース監視→header付与→durable-logへ耐久"
    "tracker: 入力/差分/判定/通知素材を audit bundle で束ねる"
  ];

  nonGoal = [
    "重要度判定ロジックの恒久化/通知ハブの名簿管理"
  ];

  meta = {
    owner = [ "@you" ];
    lifecycle = "experimental";
  };

  output = {
    packages = [];
    apps = [];
    modules = [];
    overlays = [];
    devShells = [];
  };
}