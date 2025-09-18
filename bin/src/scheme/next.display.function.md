# 関数型の機能的依存関係表示の修正タスク

```log
/home/nixos/schemeで作業するにあたり 先んじて、 /home/nixos/claude/yymmdd.hhmm.mdに、以降の目的を記述してタスク整理しながら一緒に進めよう 以下上記schemeディレクトリ配下である
この作業の結果以下の状態が期待される
以下のコマンドを実行して ./src/interface/cli.ts function-deps --format=grid next.mdに沿って目的となる表示を確認してほしい 
その後修正前のコマンド結果と修正後想定するコマンド結果をそれぞれ見せて
```

## 問題の再現方法

以下のコマンドを実行すると問題が確認できます：

```sh
cd /home/nixos/scheme && ./src/interface/cli.ts function-deps --format=grid
```

上記コマンドを実行すると、以下の問題が再現されます：

1. 最上位関数（UserAuthentication）から矢印が開始しないで、GenerateAuthTokenから矢印が開始しているように見える
2. UserAuthentication.Function 以外の関数型のファイルパスが表示されていない
3. 不要な凡例が表示されている

### 現在の表示例

```
/src/ui/authentication/UserAuthenticationUI.ts:::UserAuthenticationUI.Function                                --
/src/usecase/authentication/UserAuthenticationUsecase.ts:::UserAuthenticationUsecase.Function                 --┌-
/src/userauthentication/UserAuthentication.js:::UserAuthentication.Function                                     |-
/src/application/authentication/UserAuthenticationApplication.ts:::UserAuthenticationApplication.Function     --|-
/src/service/authentication/UserAuthenticationService.ts:::UserAuthenticationService.Function                 -- -
```

## 現状の課題

1. 依存関係グラフのレイアウトが直感的でない
   - 最上位関数（UserAuthentication）から矢印が始まっていない
   - 依存関係の方向が明確でない
   - 実行順序に従った左から右への流れが表現できていない

2. 関数型のファイルパス表示に問題がある
   - UserAuthentication.Function 以外の型のファイルパスが省略されている

3. 不要な凡例が表示されている

## 目標とする表示形式
※FUNCTION DISPLAY SPECを確認すること
※現在はUI層から他のすべてのファイルを呼び出している表示例を示しているが、実際の依存関係に合わせること
```
/src/ui/authentication/UserAuthenticationUI.ts:::UserAuthenticationUI.Function                                →  →  →  →  →
/src/usecase/authentication/UserAuthenticationUsecase.ts:::UserAuthenticationUsecase.Function                  └┘ || || ||
/src/userauthentication/UserAuthentication.js:::UserAuthentication.Function                                       └┘ || ||
/src/application/authentication/UserAuthenticationApplication.ts:::UserAuthenticationApplication.Function            └┘ ||
/src/service/authentication/UserAuthenticationService.ts:::UserAuthenticationService.Function                           └┘
```

- 最上位関数から矢印が明確に始まる
- 依存関係の方向が視覚的に明確
- 実行順序に従った左から右への流れ
- すべての関数型にファイルパスを表示
- 凡例の表示を省略
- /path/to/xxxには、各型が定義しているファイルパスがそれぞれ

## 確認が必要なファイル

/home/nixos/claude/20250323.1200.md - 作成した作業記録ファイル
/home/nixos/scheme/next.md - 修正タスクの仕様書
/home/nixos/scheme/src/interface/cli.ts - CLIのエントリーポイント
/home/nixos/scheme/src/domain/service/dependencyGraphVisualizer.ts - 依存関係グラフの可視化ロジック
/home/nixos/scheme/src/application/functionDependencyCommand.ts - 関数依存関係コマンドの実装
/home/nixos/scheme/src/interface/cli/cliController.ts - CLIコントローラー
/home/nixos/scheme/src/domain/service/functionDependencyAnalyzer.ts - 関数依存関係の解析ロジック
