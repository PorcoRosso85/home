generate_design_user_prompts=(
1.
Design.leanの目的は 
フォーマットにそって
Refer.leanファイルの機能を ./Data/Design.leanファイルでドキュメント化することである 
ドキュメント化情報を格納する ./Data/Design.leanのために
必要な新たなinductive型を定義したleanコードを提示してほしい

例:
'
before:
Requirement: []
Goal: [Purpose, Plan]
Plan: [Requirement]
Purpose: []

after:
Requirement: [GetInductiveTypeDeps]
Goal: [Purpose, Plan]
Plan: [Requirement]
Purpose: []
'

上記の例は新しくGetInductiveTypeDepsを定義し
Requirementに依存させた
こうすることでRefer.leanファイルが
この機能を提供するためのものであることがドキュメンテーションされていくことになる 
上記の例での差分以外にも
Refer.leanファイルが目指す目的と 
そのための実装があるはずなので 
./Data/Design.leanのために
必要な新たなinductive型を定義したleanコードを提示してほしい
またRequirement型にそれらへの依存させることを忘れないこと

2.
ここまで完了したのち
一度自らの回答を
1に沿っているかどうか見直すこと
目的に沿っていない場合
そのコードを修正することも可能であるので
修正・改善すること

3.
2の確認ののち
最終コードを決定したら
最終コードで作成された型が
さらに依存する型がないか確認すること
依存する型がある場合それをドキュメンテーションしなければならない
なお依存とは1の例でいうところの
'Requirement: [GetInductiveTypeDeps]'のことである
RequirementはGetInduvtiveTypeDepsを要素として成立しているため
依存しているといえる
そのためこの段階は1に戻ることを意味する

4.
1-2-3=1-2-3=1-2と繰り返したら終了すること
)
