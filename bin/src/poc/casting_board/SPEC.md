# casting_board 仕様書

## 設計原則

「ヒトはリソースの一種である」という原則を徹底し、特定の業界知識を排除した、汎用的なドメインモデルを設計する。これは、WFM（ワークフォースマネジメント）、FSM（フィールドサービスマネジメント）、PSA（プロジェクトサービスオートメーション）など、リソース割り当てが発生するあらゆる領域の基盤となりうるモデルである。

## ドメインモデル (汎用リソース割り当て版)

### 2. ドメイン層 (Domain Layer)

#### 2.1. ドメインモデル (Entities, Value Objects, Aggregates)

##### 2.1.1. Plan (Aggregate Root)
責務: 特定のコンテキストにおけるリソース割り当て計画全体の整合性を維持する。この集約内の全ての変更は、Planオブジェクトを通じて行われる。

例: "来週のシフト計画"、"プロジェクトXのタスク計画"

- id: PlanId
- name: String
- timeFrame: TimeSlot - この計画が対象とする期間
- workItems: List<WorkItem> - この計画に含まれる全ての作業項目
- assignments: List<Assignment> - この計画内で行われた全ての割り当て

**メソッド (ビジネスルール)**
- assign(resource: Resource, workItem: WorkItem): Result
  - リソースが保有する能力が、作業項目の要求能力を満たしているか検証
  - リソースの可用性（時間）を作業項目の時間枠が満たしているか検証
  - この計画内で、リソースが既に他の作業に割り当てられていないか（ダブルブッキング）検証
- unassign(assignment: Assignment): Result

##### 2.1.2. Resource (Entity)
責務: 割り当て可能な対象。ヒト、機材、車両、会議室など全てを抽象化。

- id: ResourceId
- name: String
- resourceType: ResourceType - これが 'HUMAN', 'EQUIPMENT' などを示す
- capabilities: List<Capability> - このリソースが保有する能力のリスト
- availability: Calendar - このリソースが利用可能な時間帯のリスト

##### 2.1.3. WorkItem (Entity)
責務: 完了されるべき作業の単位。

- id: WorkItemId
- description: String
- timeSlot: TimeSlot - この作業が行われるべき時間枠
- requiredCapabilities: List<CapabilityRequirement> - この作業を遂行するために要求される能力
- status: WorkItemStatus - (OPEN, ASSIGNED, IN_PROGRESS, COMPLETED)

##### 2.1.4. Assignment (Entity)
責務: 特定のリソースと特定の作業項目の具体的な結びつきを表現する。

- id: AssignmentId
- resourceId: ResourceId
- workItemId: WorkItemId
- assignedTimeSlot: TimeSlot - 実際に割り当てられた時間

##### 2.1.5. Value Objects (属性を記述する不変オブジェクト)
- ResourceType: { name: String } - 例: 'HUMAN', 'EQUIPMENT', 'VEHICLE'
- Capability: { name: String, level: Integer } - 例: {'PYTHON_SKILL', 5}, {'LOAD_CAPACITY_KG', 1000}
- CapabilityRequirement: { name: String, minimumLevel: Integer } - 要求される能力
- TimeSlot: { startTime: DateTime, endTime: DateTime } - 時間枠

## 主要な設計思想の解説

### Resourceの抽象化
このモデルの核心です。Personというエンティティは存在しません。代わりに汎用的なResourceエンティティを定義し、その性質をResourceTypeという値オブジェクトで表現します。これにより、「ヒト」はResourceTypeが 'HUMAN' であるResourceインスタンスとして扱われます。同様に、フォークリフトは 'EQUIPMENT'、配送トラックは 'VEHICLE' として、全く同じResourceの枠組みで管理できます。

### Capabilityによる能力の表現
「スキル」や「資格」という言葉を避け、より汎用的なCapability（能力）という言葉を採用しました。これにより、ヒトの「プログラミングスキル」と、機材の「最大積載量」や「稼働温度範囲」といった能力を、同じCapabilityオブジェクトで表現できます。WorkItemは特定のCapabilityを要求し、Resourceは特定のCapabilityを保有するという、シンプルなマッチングロジックに帰着します。

### Planによる整合性の保証 (Aggregate Root)
リソース割り当ての正しさは、個々の割り当てだけを見ては判断できません。「AさんをタスクXに割り当てる」という行為が正しいかどうかは、「来週のシフト計画」という全体像（Plan）の中で、Aさんが他に割り当てられていないかを確認して初めて保証できます。PlanをAggregate Root（集約の根）として設定し、全ての割り当て操作をPlanのメソッド経由で行わせることで、この計画内でのダブルブッキングやルール違反をモデルレベルで防ぎます。

### Value Objectの活用
TimeSlotやCapabilityのように、それ自体が誰かという「ID」を持たず、その「値」にのみ意味があるものはValue Objectとして設計します。これにより、システムのロジックがシンプルになり、不変性が保証されるため、意図しない副作用を防ぐことができます。

このドメインモデルは、特定の業界やビジネスプロセスに依存しないため、高い再利用性と拡張性を持ちます。「ヒトもリソースの一つ」というビジネス上の洞察を、ソフトウェアの構造として忠実に表現したものです。