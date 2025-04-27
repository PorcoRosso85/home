// 関数型メタスキーマのグラフデータベース定義
// Function.meta.json をグラフモデルに変換したDDL

// ノードテーブル定義
CREATE NODE TABLE Function (
  title STRING,
  description STRING,
  type STRING,
  async BOOLEAN,
  pure BOOLEAN DEFAULT TRUE,
  curried BOOLEAN DEFAULT FALSE,
  lazy BOOLEAN DEFAULT FALSE,
  memoization BOOLEAN DEFAULT FALSE,
  deprecated BOOLEAN DEFAULT FALSE,
  deprecationMessage STRING,
  PRIMARY KEY (title)
);

CREATE NODE TABLE Parameter (
  name STRING,
  type STRING,
  description STRING,
  required BOOLEAN,
  immutable BOOLEAN DEFAULT TRUE,
  default_value STRING,
  PRIMARY KEY (name, type)
);

CREATE NODE TABLE ReturnType (
  type STRING,
  description STRING,
  immutable BOOLEAN DEFAULT TRUE,
  PRIMARY KEY (type)
);

CREATE NODE TABLE Exception (
  name STRING,
  description STRING,
  code STRING,
  PRIMARY KEY (name)
);

CREATE NODE TABLE Example (
  id INT64,
  description STRING,
  input STRING,
  output STRING,
  PRIMARY KEY (id)
);

CREATE NODE TABLE RecursionInfo (
  isRecursive BOOLEAN DEFAULT FALSE,
  tailRecursive BOOLEAN DEFAULT FALSE, 
  recursionType STRING,
  terminationCondition STRING,
  structuralRecursion BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (isRecursive, recursionType)
);

CREATE NODE TABLE ComplexityAnalysis (
  id INT64,
  time STRING,
  space STRING,
  PRIMARY KEY (id)
);

CREATE NODE TABLE RecursionDepth (
  maximum INT64,
  average FLOAT64,
  description STRING,
  PRIMARY KEY (maximum)
);

CREATE NODE TABLE TransformationType (
  type STRING PRIMARY KEY
);

CREATE NODE TABLE Invariant (
  id INT64,
  description STRING,
  PRIMARY KEY (id)
);

// リレーションシップテーブル定義
CREATE REL TABLE HasParameter (
  FROM Function TO Parameter,
  required BOOLEAN
);

CREATE REL TABLE ReturnsType (
  FROM Function TO ReturnType
);

CREATE REL TABLE ThrowsException (
  FROM Function TO Exception
);

CREATE REL TABLE HasExample (
  FROM Function TO Example
);

CREATE REL TABLE HasRecursionInfo (
  FROM Function TO RecursionInfo
);

CREATE REL TABLE HasComplexityAnalysis (
  FROM RecursionInfo TO ComplexityAnalysis
);

CREATE REL TABLE DependsOn (
  FROM Function TO Function,
  description STRING
);

CREATE REL TABLE MutuallyRecursiveWith (
  FROM Function TO Function
);

CREATE REL TABLE HasNestedParameter (
  FROM Parameter TO Parameter
);

CREATE REL TABLE HasRecursionDepth (
  FROM RecursionInfo TO RecursionDepth
);

CREATE REL TABLE HasTransformationType (
  FROM RecursionInfo TO TransformationType
);

CREATE REL TABLE HasInvariant (
  FROM RecursionInfo TO Invariant
);

CREATE REL TABLE HasIntermediateStep (
  FROM Example TO IntermediateStep
);

CREATE NODE TABLE IntermediateStep (
  id INT64,
  stepName STRING,
  value STRING,
  PRIMARY KEY (id)
);
