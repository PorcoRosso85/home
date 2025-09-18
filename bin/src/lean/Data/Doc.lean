def planInitial_title : IO Unit := IO.println "計画初期"

def requirements_title : IO Unit := IO.println "要件"

def purpose_title : IO Unit := IO.println "目的"
def purpose_content : IO Unit := IO.println "型の依存関係をグラフ構造化し、型に沿った実装を可能にする情報を格納\n格納された情報をクエリ可能にする"
def purpose : IO Unit := do
  purpose_title
  purpose_content
#eval purpose

def functionalRequirements_title : IO Unit := IO.println "機能要件"

def typeDefinitionSyntaxList_title : IO Unit := IO.println "型定義構文の網羅的なリストアップ"

def inductive_item : IO Unit := IO.println "inductive"
def structure_item : IO Unit := IO.println "structure"
def class_item : IO Unit := IO.println "class"
def others_item : IO Unit := IO.println "その他 (alias, opaque, theorem, def など)"
def typeDefinitionSyntaxList_content : IO Unit := do
  inductive_item
  structure_item
  class_item
  others_item
def typeDefinitionSyntaxList : IO Unit := do
  typeDefinitionSyntaxList_title
  typeDefinitionSyntaxList_content
#eval typeDefinitionSyntaxList

def multipleFileTypeDefHandling_title : IO Unit := IO.println "複数ファイルに跨る型定義の取り扱い"

def singleLeanFile_item : IO Unit := IO.println "単一leanファイル"
def ignoreDependencies_item : IO Unit := IO.println "依存関係は考慮せず全てデータとして扱う"
def typeDefinitionLimit_item : IO Unit := IO.println "型定義数: 1000以下を想定"
def multipleFileTypeDefHandling_content : IO Unit := do
  singleLeanFile_item
  ignoreDependencies_item
  typeDefinitionLimit_item
def multipleFileTypeDefHandling : IO Unit := do
  multipleFileTypeDefHandling_title
  multipleFileTypeDefHandling_content

def typeDependencyGranularity_title : IO Unit := IO.println "型定義の依存関係の粒度"

def memberLevelDependency_item : IO Unit := IO.println "メンバーレベルの依存関係 (例: User型のnameフィールドがString 型に依存)"
def typeDependencyGranularity_content : IO Unit := do
  memberLevelDependency_item
def typeDependencyGranularity : IO Unit := do
  typeDependencyGranularity_title
  typeDependencyGranularity_content

def dependencyRepresentationFormat_title : IO Unit := IO.println "依存関係の表現形式"

def graphStructure_item : IO Unit := IO.println "グラフ構造 (ノードとエッジ)"
def sqliteDataFormat_item : IO Unit := IO.println "データ形式: SQLite を検討"
def dependencyRepresentationFormat_content : IO Unit := do
  graphStructure_item
  sqliteDataFormat_item
def dependencyRepresentationFormat : IO Unit := do
  dependencyRepresentationFormat_title
  dependencyRepresentationFormat_content

def queryType_title : IO Unit := IO.println "クエリの種類"

def dependentTypeList_item : IO Unit := IO.println "特定の型が依存する型の一覧を取得"
def dependingTypeList_item : IO Unit := IO.println "特定の型に依存する型の一覧を取得"
def graphStructureQuery_item : IO Unit := IO.println "型定義全体のグラフ構造を取得"
def typeDetailInfoQuery_item : IO Unit := IO.println "特定の型の詳細情報 (定義、依存関係など) を取得"
def queryType_content : IO Unit := do
  dependentTypeList_item
  dependingTypeList_item
  graphStructureQuery_item
  typeDetailInfoQuery_item
def queryType : IO Unit := do
  queryType_title
  queryType_content

def leanFilePathNamingRule_title : IO Unit := IO.println "leanファイル (データファイル) の配置場所、命名規則"

def relativePathFromProjectRoot_item : IO Unit := IO.println "プロジェクトルートからの相対パスで指定"
def dataSubdirectory_item : IO Unit := IO.println "`./Data` 配下に配置"
def leanFilePathNamingRule_content : IO Unit := do
  relativePathFromProjectRoot_item
  dataSubdirectory_item
def leanFilePathNamingRule : IO Unit := do
  leanFilePathNamingRule_title
  leanFilePathNamingRule_content

def databaseType_title : IO Unit := IO.println "データベースの種類"

def sqlite_item : IO Unit := IO.println "SQLite"
def sqliteReason_item : IO Unit := IO.println "選定理由: ローカル動作限定の想定"
def databaseType_content : IO Unit := do
  sqlite_item
  sqliteReason_item
def databaseType : IO Unit := do
  databaseType_title
  databaseType_content

def errorHandlering_title : IO Unit := IO.println "エラーハンドリング"

def errorTypeDef_item : IO Unit := IO.println "エラー型定義を行う"
def errorCategoryList_item : IO Unit := IO.println "エラーの種類をカテゴライズし一覧化"

def invalidTypeDefSyntax_item : IO Unit := IO.println "    型定義構文が不正な場合 (IOError型？)"
def dependencyExtractionFailure_item : IO Unit := IO.println "    依存関係抽出失敗"
def databaseStorageFailure_item : IO Unit := IO.println "    データベース格納失敗 (DatabaseError型？)"
def queryExecutionError_item : IO Unit := IO.println "    クエリ実行時エラー (DatabaseError型？)"
def errorCategoryList_content : IO Unit := do
  invalidTypeDefSyntax_item
  dependencyExtractionFailure_item
  databaseStorageFailure_item
  queryExecutionError_item
def errorHandlering_content : IO Unit := do
  errorTypeDef_item
  errorCategoryList_item
  errorCategoryList_content
def errorHandlering : IO Unit := do
  errorHandlering_title
  errorHandlering_content

def functionalRequirements_content : IO Unit := do
  typeDefinitionSyntaxList
  multipleFileTypeDefHandling
  typeDependencyGranularity
  dependencyRepresentationFormat
  queryType
  leanFilePathNamingRule
  databaseType
  errorHandlering
def functionalRequirements : IO Unit := do
  functionalRequirements_title
  functionalRequirements_content

def requirements_content : IO Unit := do
  purpose
  functionalRequirements
def requirements : IO Unit := do
  requirements_title
  requirements_content

def design_title : IO Unit := IO.println "### 設計"

def typeDefFileParsing_title : IO Unit := IO.println "型定義ファイル (leanファイル) のパース処理"

def utilizeLeanParser_item : IO Unit := IO.println "Leanのパーサー機能を活用\n    * [ref/meta.yaml#introduction](https://leanprover-community.github.io/lean4-metaprogramming-book/#introduction)\n    * [ref/meta.yaml#overview](https://leanprover-community.github.io/lean4-metaprogramming-book/main/02_overview.html)\n    * [ref/meta.yaml#elaboration](https://leanprover-community.github.io/lean4-metaprogramming-book/main/07_elaboration.html)\n    * [ref/meta.yaml#syntax](https://leanprover-community.github.io/lean4-metaprogramming-book/main/05_syntax.html)\n    * [ref/meta.yaml#metam](https://leanprover-community.github.io/lean4-metaprogramming-book/main/04_metam.html)k"
def typeDefFileParsing_content : IO Unit := do
  utilizeLeanParser_item
def typeDefFileParsing : IO Unit := do
  typeDefFileParsing_title
  typeDefFileParsing_content

def getTypeDefListFromLeanEnv_title : IO Unit := IO.println "`CoreM`, `MetaM` を利用しLean環境から型定義一覧を取得"

def extractTypeDefFromEnv_item : IO Unit := IO.println "    `Environment` から `inductive`, `structure`, `class` などの型定義を抽出"
def addAliasOpaqueTheoremDefParsing_item : IO Unit := IO.println "    `alias`, `opaque`, `theorem`, `def` 構文のパー ス処理を追加"
def specifyInfoToAcquireFromSyntax_item : IO Unit := IO.println "    各構文から取得する情報を明記 (例: `theorem` は型情報のみ)"
def getTypeDefListFromLeanEnv_content : IO Unit := do
  extractTypeDefFromEnv_item
  addAliasOpaqueTheoremDefParsing_item
  specifyInfoToAcquireFromSyntax_item
def getTypeDefListFromLeanEnv : IO Unit := do
  getTypeDefListFromLeanEnv_title
  getTypeDefListFromLeanEnv_content

def getDetailInfoOfTypeDef_title : IO Unit := IO.println "各型定義の詳細情報取得"

def getDetailInfoByGetConstInfo_item : IO Unit := IO.println "    型名から `getConstInfo` で詳細情報 (`ConstantInfo`) を取得"

def constantInfoIncludesTypeValue_item : IO Unit := IO.println "        `ConstantInfo` には `type`, `value` などが 含まれる"
def getDetailInfoByGetConstInfo_content : IO Unit := do
  constantInfoIncludesTypeValue_item
def getDetailInfoOfTypeDef_content : IO Unit := do
  getDetailInfoByGetConstInfo_item
  getDetailInfoByGetConstInfo_content
def getDetailInfoOfTypeDef : IO Unit := do
  getDetailInfoOfTypeDef_title
  getDetailInfoOfTypeDef_content

def typeDefFileParsing_content_2 : IO Unit := do
  typeDefFileParsing
  getTypeDefListFromLeanEnv
  getDetailInfoOfTypeDef
def typeDefFileParsing_2 : IO Unit := do
  typeDefFileParsing_title
  typeDefFileParsing_content_2

def exprOperationOfTypeInfo_title : IO Unit := IO.println "型情報の `Expr` 操作"

def operateTypeInfoAsExpr_item : IO Unit := IO.println "`ConstantInfo` から取得した型情報を `Expr` として操作"
def simplifyInfoExtractionByTypeReduction_item : IO Unit := IO.println "`instantiateMVars`, `reduce`, `whnf` などで型を簡約化、情報抽出"
def exprOperationOfTypeInfo_content : IO Unit := do
  operateTypeInfoAsExpr_item
  simplifyInfoExtractionByTypeReduction_item
def exprOperationOfTypeInfo : IO Unit := do
  exprOperationOfTypeInfo_title
  exprOperationOfTypeInfo_content

def dependencyAnalysis_title : IO Unit := IO.println "依存関係解析"

def analyzeDependencyFromExprOfTypeInfo_item : IO Unit := IO.println "型情報 (`type`, `value`) の `Expr` を解析し依存関係を抽出"
def analyzeDependencyByTypeDecomposition_item : IO Unit := IO.println "`forallTelescope` などで関数の型を分解し、引数・返り値の型から依存関係を分析"
def extractMemberLevelDependency_item : IO Unit := IO.println "メンバーレベルの依存関係を抽出"
def dependencyAnalysis_content : IO Unit := do
  analyzeDependencyFromExprOfTypeInfo_item
  analyzeDependencyByTypeDecomposition_item
  extractMemberLevelDependency_item
def dependencyAnalysis : IO Unit := do
  dependencyAnalysis_title
  dependencyAnalysis_content

def structureDependencyAnalysisResultAndOutput_title : IO Unit := IO.println "依存関係の構造化と出力"

def outputDependencyAnalysisResultAsGraph_item : IO Unit := IO.println "依存関係の解析結果をグラフ構造で表現し出力"
def considerSqliteDataFormat_item : IO Unit := IO.println "データ形式: SQLite を検討"
def representWithNodesAndEdges_item : IO Unit := IO.println "ノードとエッジで表現 (ノード: 型定義、エッジ: 依存関係)"
def structureDependencyAnalysisResultAndOutput_content : IO Unit := do
  outputDependencyAnalysisResultAsGraph_item
  considerSqliteDataFormat_item
  representWithNodesAndEdges_item
def structureDependencyAnalysisResultAndOutput : IO Unit := do
  structureDependencyAnalysisResultAndOutput_title
  structureDependencyAnalysisResultAndOutput_content

def databaseSchemaDesign_title : IO Unit := IO.println "データベーススキーマ設計"

def structureTable_item : IO Unit := IO.println "Structure テーブル (型定義情報を格納)"
def dependencyTable_item : IO Unit := IO.println "Dependency テーブル (依存関係をエッジとして表現)"

def representWithDirectedGraph_item : IO Unit := IO.println "    有向グラフで表現"
def dependencyTable_content : IO Unit := do
  representWithDirectedGraph_item
def graphDataStructure_item : IO Unit := IO.println "2.5.3. グラフデータ構造"

def nodeTypeDefFilePathLineNumberDetailInfo_item : IO Unit := IO.println "    ノード: 型定義 (型名、定義ファイルパス 、定義行数、詳細情報)"
def edgeDependencySourceToTargetTypeDependencyType_item : IO Unit := IO.println "    エッジ: 依存関係 (依存元型 -> 依存先型、依存の種類)"
def clarifyTableColumnTypeDef_item : IO Unit := IO.println "    テーブルのカラム定義、データ型を明確化"
def considerIndexDesignForQueryEfficiency_item : IO Unit := IO.println "    クエリ効率向上のためのインデックス設計を 検討"
def describeNodeAndEdgeAttributesSpecifically_item : IO Unit := IO.println "    ノードとエッジの属性を具体的に記述 (TODO に移動)"
def graphDataStructure_content : IO Unit := do
  nodeTypeDefFilePathLineNumberDetailInfo_item
  edgeDependencySourceToTargetTypeDependencyType_item
  clarifyTableColumnTypeDef_item
  considerIndexDesignForQueryEfficiency_item
  describeNodeAndEdgeAttributesSpecifically_item
def databaseSchemaDesign_content : IO Unit := do
  structureTable_item
  dependencyTable_item
  dependencyTable_content
  graphDataStructure_item
  graphDataStructure_content
def databaseSchemaDesign : IO Unit := do
  databaseSchemaDesign_title
  databaseSchemaDesign_content

def errorHandleringDesign_title : IO Unit := IO.println "エラー処理設計"

def addErrorTypeListExampleLogPolicyTableToTodo_item : IO Unit := IO.println "エラーの種類とエラー型、エラーメッセージ 例、ログ出力例、処理方針をまとめた表を追加 (TODO に移動)"
def categorizeErrorTypeAndReflectToTypeDef_item : IO Unit := IO.println "エラーの種類をカテゴライズしエラー型定義に反映"
def illustrateOrDescribeErrorProcessingFlow_item : IO Unit := IO.println "エラー発生時の処理フローを設計ドキュメントに 図示またはテキストで記述 (TODO に移動)"
def errorHandleringDesign_content : IO Unit := do
  addErrorTypeListExampleLogPolicyTableToTodo_item
  categorizeErrorTypeAndReflectToTypeDef_item
  illustrateOrDescribeErrorProcessingFlow_item
def errorHandleringDesign : IO Unit := do
  errorHandleringDesign_title
  errorHandleringDesign_content

def testDesign_title : IO Unit := IO.println "テスト設計"

def unitTestIntegrationTestE2eTest_item : IO Unit := IO.println "単体テスト、結合テスト、E2Eテスト"
def createTestCaseNormalAbnormal_item : IO Unit := IO.println "テストケース作成 (正常系、異常系)"
def testDesign_content : IO Unit := do
  unitTestIntegrationTestE2eTest_item
  createTestCaseNormalAbnormal_item
def testDesign : IO Unit := do
  testDesign_title
  testDesign_content

def documentCreation_title : IO Unit := IO.println "ドキュメント作成"

def designDocumentArchitectureDataModelApiSpec_item : IO Unit := IO.println "設計ドキュメント (アーキテクチャ、データモデル、API仕様)"
def userManualInstallUsageQueryExample_item : IO Unit := IO.println "ユーザーマニュアル (インストール、使い方、クエリ例)"
def documentCreation_content : IO Unit := do
  designDocumentArchitectureDataModelApiSpec_item
  userManualInstallUsageQueryExample_item
def documentCreation : IO Unit := do
  documentCreation_title
  documentCreation_content

def directoryStructure_title : IO Unit := IO.println "ディレクトリ構成"

def addSpecificNamingRuleExampleDivideDirByTypeCategory_item : IO Unit := IO.println "具体的な命名規則を追記 (例: 型カ テゴリごとにディレクトリ分割)"
def exampleDataInductiveNatLeanDataStructureListLean_item : IO Unit := IO.println "例: `./Data/Inductive/Nat.lean`, `./Data/Structure/List.lean`"
def directoryStructure_content : IO Unit := do
  addSpecificNamingRuleExampleDivideDirByTypeCategory_item
  exampleDataInductiveNatLeanDataStructureListLean_item
def directoryStructure : IO Unit := do
  directoryStructure_title
  directoryStructure_content

def todo_title : IO Unit := IO.println "TODO"

def howToUtilizeLeanParserFeature_title : IO Unit := IO.println "**Leanパーサー機能の活用方法**:"

def describeFunctionNameOfLeanParserApiToUtilize_item : IO Unit := IO.println "    利用する Lean パーサーAPI の関数 名を記述"
def addParseCodeExamplePseudoCodeOrLeanCodeSnippet_item : IO Unit := IO.println "    パース処理のコード例 (pseudo-code or Lean code snippet) を追加"
def howToUtilizeLeanParserFeature_content : IO Unit := do
  describeFunctionNameOfLeanParserApiToUtilize_item
  addParseCodeExamplePseudoCodeOrLeanCodeSnippet_item
def howToUtilizeLeanParserFeature : IO Unit := do
  howToUtilizeLeanParserFeature_title
  howToUtilizeLeanParserFeature_content

def concreteExampleOfExprOperationOfTypeInfo_title : IO Unit := IO.println "**型情報のExpr操作の具体例**:"

def addConcreteCodeExampleOrProcessingFlowOfTypeOperationFunction_item : IO Unit := IO.println "    `Expr` 操作関数 の具体的なコード例や処理フローを追記"
def addExampleOfTypeInfoAcquiredByGetConstInfoAndSimplifiedByWhnf_item : IO Unit := IO.println "    `getConstInfo`  で取得した `ConstantInfo` から `type` 情報を取得し、`whnf` で簡約化する例などを追加"
def addExampleOfInstantiateMVarsReduceApplicationInDependencyAnalysisProcess_item : IO Unit := IO.println "    依存 関係解析処理における `instantiateMVars` や `reduce` の適用例を追加"
def concreteExampleOfExprOperationOfTypeInfo_content : IO Unit := do
  addConcreteCodeExampleOrProcessingFlowOfTypeOperationFunction_item
  addExampleOfTypeInfoAcquiredByGetConstInfoAndSimplifiedByWhnf_item
  addExampleOfInstantiateMVarsReduceApplicationInDependencyAnalysisProcess_item
def concreteExampleOfExprOperationOfTypeInfo : IO Unit := do
  concreteExampleOfExprOperationOfTypeInfo_title
  concreteExampleOfExprOperationOfTypeInfo_content

def describeNodeAndEdgeAttributesOfGraphDataStructureInDetail_item : IO Unit := IO.println "2.5.3.5. グラフデータ構造 のノードとエッジの属性を詳細に記述"
def addTableSummarizingErrorTypeListExampleLogPolicy_item : IO Unit := IO.println "2.6.1. エラーの種類とエラー型、エラーメッセージ例、ログ出力例、処理方針をまとめた表を追加"
def illustrateOrDescribeProcessingFlowAtErrorOccurrenceInDesignDocument_item : IO Unit := IO.println "2.6.3. エラー発 生時の処理フローを設計ドキュメントに図示またはテキストで記述"
def todo_content : IO Unit := do
  howToUtilizeLeanParserFeature
  concreteExampleOfExprOperationOfTypeInfo
  IO.println "2.10.3. 2.5.3.5. グラフデータ構造のノードとエッジの属性を詳細に記述"
  IO.println "2.10.4. 2.6.1. エラーの種類とエラー型、エラーメッセージ例、ログ出力例、処理方針をまとめた表を追加"
  IO.println "2.10.5. 2.6.3. エラー発生時の処理フローを設計ドキュメントに図示またはテキストで記述"
def todo : IO Unit := do
  todo_title
  todo_content

def design_content : IO Unit := do
  typeDefFileParsing_2
  exprOperationOfTypeInfo
  dependencyAnalysis
  structureDependencyAnalysisResultAndOutput
  databaseSchemaDesign
  errorHandleringDesign
  testDesign
  documentCreation
  directoryStructure
  todo
def design : IO Unit := do
  design_title
  design_content

def planInitial_content : IO Unit := do
  requirements
  design
def planInitial : IO Unit := do
  planInitial_title
  planInitial_content

def planMediumTerm_title : IO Unit := IO.println "## 計画中期"

def requirements_title_2 : IO Unit := IO.println "要件"

def nonFunctionalRequirements_title : IO Unit := IO.println "非機能要件"

def performanceRequirements_title : IO Unit := IO.println "パフォーマンス要件"

def typeDefFileLoadingTime_item : IO Unit := IO.println "4.1.1.1. 型定義ファイル読み込み時間"
def dependencyExtractionTime_item : IO Unit := IO.println "4.1.1.2. 依存関係抽出時間"
def databaseStorageTime_item : IO Unit := IO.println "4.1.1.3. データベース格納時間"
def queryResponseTime_item : IO Unit := IO.println "4.1.1.4. クエリ応答時間"
def specifyNumericalTargetIfAny_item : IO Unit := IO.println "4.1.1.5. 具体的な数値目標があれば明記"
def performanceRequirements_content : IO Unit := do
  typeDefFileLoadingTime_item
  dependencyExtractionTime_item
  databaseStorageTime_item
  queryResponseTime_item
  specifyNumericalTargetIfAny_item
def performanceRequirements : IO Unit := do
  performanceRequirements_title
  performanceRequirements_content

def scalabilityRequirements_title : IO Unit := IO.println "スケーラビリティ要件"

def performanceDegradationToleranceWhenTypeDefCountIncreases_item : IO Unit := IO.println "4.1.2.1. 型定義数増加時の性能劣化許容範囲"
def performanceDegradationToleranceWhenDataVolumeIncreases_item : IO Unit := IO.println "4.1.2.2. データ量増加時の性能劣化許容範囲"
def scalabilityRequirements_content : IO Unit := do
  performanceDegradationToleranceWhenTypeDefCountIncreases_item
  performanceDegradationToleranceWhenDataVolumeIncreases_item
def scalabilityRequirements : IO Unit := do
  scalabilityRequirements_title
  scalabilityRequirements_content

def securityRequirements_title : IO Unit := IO.println "セキュリティ要件"

def accessControlToData_item : IO Unit := IO.println "4.1.3.1. データへのアクセス制御"
def accessControlToDatabase_item : IO Unit := IO.println "4.1.3.2. データベースへのアクセス制御"
def securityRequirements_content : IO Unit := do
  accessControlToData_item
  accessControlToDatabase_item
def securityRequirements : IO Unit := do
  securityRequirements_title
  securityRequirements_content

def maintainabilityConservability_title : IO Unit := IO.println "メンテナンス性・保守性"

def codeReadabilityConservability_item : IO Unit := IO.println "4.1.4.1. コードの可読性、保守性"
def documentMaintenance_item : IO Unit := IO.println "4.1.4.2. ドキュメントの整備"
def testCodeCompleteness_item : IO Unit := IO.println "4.1.4.3. テストコードの充実"
def maintainabilityConservability_content : IO Unit := do
  codeReadabilityConservability_item
  documentMaintenance_item
  testCodeCompleteness_item
def maintainabilityConservability : IO Unit := do
  maintainabilityConservability_title
  maintainabilityConservability_content

def extensibility_title : IO Unit := IO.println "拡張性"

def supportForNewTypeDefSyntax_item : IO Unit := IO.println "4.1.5.1. 新しい型定義構文への対応"
def additionOfNewQueryType_item : IO Unit := IO.println "4.1.5.2. 新しいクエリ種類の追加"
def cooperationWithOtherToolsExampleVisualizationTool_item : IO Unit := IO.println "4.1.5.3. 他のツールとの連携 (例: 可視化ツ ール)"
def extensibility_content : IO Unit := do
  supportForNewTypeDefSyntax_item
  additionOfNewQueryType_item
  cooperationWithOtherToolsExampleVisualizationTool_item
def extensibility : IO Unit := do
  extensibility_title
  extensibility_content

def uiUx_title : IO Unit := IO.println "UI/UX"

def queryExecutionMethodCommandLineInterfaceApiGui_item : IO Unit := IO.println "4.1.6.1. クエリ実行方法 (コマンドラインインターフェース、API、GUI)"
def queryResultDisplayFormat_item : IO Unit := IO.println "4.1.6.2. クエリ結果の表示形式"
def errorMessagesClarity_item : IO Unit := IO.println "4.1.6.3. エラーメッセージの分かりやすさ"
def uiUx_content : IO Unit := do
  queryExecutionMethodCommandLineInterfaceApiGui_item
  queryResultDisplayFormat_item
  errorMessagesClarity_item
def uiUx : IO Unit := do
  uiUx_title
  uiUx_content

def nonFunctionalRequirements_content : IO Unit := do
  performanceRequirements
  scalabilityRequirements
  securityRequirements
  maintainabilityConservability
  extensibility
  uiUx
def nonFunctionalRequirements : IO Unit := do
  nonFunctionalRequirements_title
  nonFunctionalRequirements_content

def requirements_content_2 : IO Unit := do
  nonFunctionalRequirements
def requirements_2 : IO Unit := do
  requirements_title_2
  requirements_content_2

def design_title_2 : IO Unit := IO.println "設計"

def performanceImprovementMeasures_title : IO Unit := IO.println "パフォーマンス改善策"

def databaseIndexDesign_item : IO Unit := IO.println "5.1.1. データベースのインデックス設計"
def queryOptimization_item : IO Unit := IO.println "5.1.2. クエリの最適化"
def introductionOfCacheMechanism_item : IO Unit := IO.println "5.1.3. キャッシュ機構の導入"
def performanceImprovementMeasures_content : IO Unit := do
  databaseIndexDesign_item
  queryOptimization_item
  introductionOfCacheMechanism_item
def performanceImprovementMeasures : IO Unit := do
  performanceImprovementMeasures_title
  performanceImprovementMeasures_content

def securityCountermeasures_title : IO Unit := IO.println "セキュリティ対策"

def accessControlToDatabaseAuthenticationAuthorization_item : IO Unit := IO.println "5.2.1. データベースへのアクセス制御 (認証、認可)"
def inputValidationSanitization_item : IO Unit := IO.println "5.2.2. 入力値の検証 (サニタイズ)"
def securityCountermeasures_content : IO Unit := do
  accessControlToDatabaseAuthenticationAuthorization_item
  inputValidationSanitization_item
def securityCountermeasures : IO Unit := do
  securityCountermeasures_title
  securityCountermeasures_content

def design_content_2 : IO Unit := do
  performanceImprovementMeasures
  securityCountermeasures
def design_2 : IO Unit := do
  design_title_2
  design_content_2

def planMediumTerm_content : IO Unit := do
  requirements_2
  design_2
def planMediumTerm : IO Unit := do
  planMediumTerm_title
  planMediumTerm_content


def main : IO Unit := do
  planInitial
  planMediumTerm
  pure ()
