mermaid図をdrawioで描写できるxmlで記述することが目的である
起点は「開始」、終点は「終了」というノード名で作成し、角が丸い長方形とすること
各処理名でノードを作成し、ひし形とすること
すべての白背景黒線枠のノードとすること
エッジは作成するが、付帯するエッジ名は作成しないこと

以下は構文サンプルであり、具体的な値は参考としてはいけない
```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- ノード定義 -->
    <mxCell id="A" value="APIエンドポイントの処理" parent="1" vertex="1">
      <mxGeometry x="50" y="50" width="150" height="40" as="geometry"/>
    </mxCell>
```
