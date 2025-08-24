#!/bin/bash
# 法人番号CSVダウンロードスクリプト
# 静岡県のデータをサンプルとして使用

set -e

DATA_DIR="./data"
mkdir -p $DATA_DIR

echo "📥 法人番号データダウンロード確認中..."
echo ""
echo "法人番号公表サイトのダウンロードページ："
echo "https://www.houjin-bangou.nta.go.jp/download/zenken/"
echo ""
echo "静岡県のCSVファイル（Unicode版）は手動でダウンロードが必要です。"
echo ""
echo "手順："
echo "1. 上記URLにアクセス"
echo "2. 「全件データダウンロード」セクション"
echo "3. 「CSV形式・Unicode」タブ"  
echo "4. 静岡県のzipファイルをダウンロード"
echo "5. $DATA_DIR/ に解凍"
echo ""
echo "または、以下のサンプルデータを作成します："

# サンプルCSV作成
cat << 'EOF' > $DATA_DIR/shizuoka_sample.csv
"sequenceNumber","corporateNumber","process","correct","updateDate","changeDate","corporateName","corporateNameKana","corporateNameEn","postalCode","prefectureCode","cityCode","streetNumber","addressOutside","addressOutsideKana","closeDate","closeCause","successorCorporateNumber","changeCauseDeatil","assignmentDate","enName","enPrefectureName","enCityName","enAddress","furigana","hihyoji"
"1","5080401000029","01","0","2015-10-05","2015-10-05","株式会社アイエイアイ","アイエイアイ","IAI Corporation","424-0103","22","22220","藁科２００－２０","","","","","","","2015-10-05","","Shizuoka-ken","Shizuoka-shi Shimizu-ku","2-20-20, Warashina","カブシキガイシャアイエイアイ","0"
"2","9080001000234","01","0","2015-10-05","2015-10-05","株式会社静岡銀行","シズオカギンコウ","THE SHIZUOKA BANK, LTD.","420-0857","22","22101","呉服町１丁目１０番地","","","","","","","2015-10-05","THE SHIZUOKA BANK, LTD.","Shizuoka-ken","Shizuoka-shi Aoi-ku","10, Gofuku-cho 1-chome","カブシキガイシャシズオカギンコウ","0"
"3","3080401001234","01","0","2015-10-05","2015-10-05","ヤマハ株式会社","ヤマハ","YAMAHA CORPORATION","430-0916","22","22202","中沢町１０番１号","","","","","","","2015-10-05","YAMAHA CORPORATION","Shizuoka-ken","Hamamatsu-shi Naka-ku","10-1, Nakazawa-cho","ヤマハカブシキガイシャ","0"
"4","5080001008999","01","0","2015-10-05","2015-10-05","スズキ株式会社","スズキ","SUZUKI MOTOR CORPORATION","432-8065","22","22202","高塚町３００番地","","","","","","","2015-10-05","SUZUKI MOTOR CORPORATION","Shizuoka-ken","Hamamatsu-shi Minami-ku","300, Takatsuka-cho","スズキカブシキガイシャ","0"
"5","6080401003456","01","0","2015-10-05","2015-10-05","株式会社資生堂","シセイドウ","Shiseido Company, Limited","420-0839","22","22101","鷹匠２丁目１５番１号","","","","","","","2015-10-05","","Shizuoka-ken","Shizuoka-shi Aoi-ku","2-15-1 Takajo","カブシキガイシャシセイドウ","0"
EOF

echo "✅ サンプルデータを作成しました: $DATA_DIR/shizuoka_sample.csv"
echo ""
echo "カラム説明："
echo "- corporateNumber: 法人番号（13桁）"
echo "- corporateName: 法人名"
echo "- prefectureCode: 都道府県コード（22=静岡）"
echo "- cityCode: 市区町村コード"
echo "- streetNumber: 所在地"