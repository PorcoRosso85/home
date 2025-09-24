{
  description = "垂直ドメイン群 - 業界・機能特化のアプリケーション層";

  goal = [
    "platform共通関節を活用したドメイン特化価値の実現"
    "業界固有要件への最短価値線提供"
  ];

  nonGoal = [
    "platformレイヤーの再実装"
    "ドメイン間の密結合"
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