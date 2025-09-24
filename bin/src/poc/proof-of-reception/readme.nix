{
  description = "Reception → Preservation → Presentation を最短経路で実現する骨格＋共通関節";

  goal = [
    "Who/When/Correlation を全入力に付与しゼロデータロスと監査再現を保証"
    "Queue+WAL+R2 を基盤に duckdb meta-index を薄く活用"
  ];

  nonGoal = [
    "巨大RDB/重厚DWH/配信名簿管理/請求書発行/IDPの提供"
    "ルール/通知の本実装（Phase2以降）"
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