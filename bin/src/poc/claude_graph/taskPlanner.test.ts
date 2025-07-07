/**
 * TaskPlanner Tests - TDD Red Phase
 * 規約準拠: 純粋関数、Result型、レイヤー分離
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.210.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.210.0/testing/bdd.ts";

// 規約準拠: ドメイン型定義
interface TaskPlan {
  id: string;
  tasks: PlannedTask[];
  totalEstimatedTime?: number;
  dependencies: DependencyGraph;
  explanation: string;
}

interface PlannedTask {
  id: string;
  type: 'implement' | 'test' | 'refactor' | 'review';
  targetId: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimatedTime?: number;
  prerequisites: string[];
  status: 'pending' | 'in_progress' | 'completed';
}

interface DependencyGraph {
  nodes: string[];
  edges: Array<{ from: string; to: string }>;
}

// 規約準拠: Result型
type PlanResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: PlanError };

type PlanError = 
  | { type: "invalid_requirement"; requirementId: string }
  | { type: "circular_dependency"; cycle: string[] }
  | { type: "exploration_failed"; message: string };

// 規約準拠: 関数型インターフェース
type PlanTasksForRequirement = (
  requirementId: string
) => Promise<PlanResult<TaskPlan>>;

type PlanUnimplementedRequirements = () => Promise<PlanResult<TaskPlan[]>>;

type PlanTasksForLocation = (
  uriPath: string
) => Promise<PlanResult<TaskPlan>>;

// 探索結果の型（taskExplorerから）
interface ExplorationData {
  nodes: Array<{
    id: string;
    type: 'requirement' | 'code' | 'test';
    title?: string;
    priority?: string;
  }>;
  relations: Array<{
    from: string;
    to: string;
    type: 'implements' | 'verifies' | 'depends_on';
  }>;
  insights: string[];
}

describe("TaskPlanner", () => {
  describe("planTasksForRequirement", () => {
    it("test_planTasksForRequirement_unimplemented_createsImplementTask", async () => {
      const mockExplore = async (reqId: string): Promise<ExplorationData> => ({
        nodes: [{ id: reqId, type: "requirement", title: "User Auth" }],
        relations: [],
        insights: ["要件 req_user_auth は未実装です。実装タスクが必要です。"]
      });
      
      const planTasks = createPlanTasksForRequirement(mockExplore);
      const result = await planTasks("req_user_auth");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        const implTask = result.data.tasks.find(t => t.type === "implement");
        assertExists(implTask);
        assertEquals(implTask?.targetId, "req_user_auth");
        assertEquals(implTask?.priority, "medium");
      }
    });

    it("test_planTasksForRequirement_untested_createsTestTask", async () => {
      const mockExplore = async (): Promise<ExplorationData> => ({
        nodes: [
          { id: "req_user_auth", type: "requirement" },
          { id: "code_123", type: "code" }
        ],
        relations: [{ from: "req_user_auth", to: "code_123", type: "implements" }],
        insights: ["要件 req_user_auth にはテストがありません。テスト作成タスクが必要です。"]
      });
      
      const planTasks = createPlanTasksForRequirement(mockExplore);
      const result = await planTasks("req_user_auth");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        const testTask = result.data.tasks.find(t => t.type === "test");
        assertExists(testTask);
        assertEquals(testTask?.prerequisites.length, 0); // 実装済みなので前提なし
      }
    });

    it("test_planTasksForRequirement_withDependencies_ordersTasksCorrectly", async () => {
      const mockExplore = async (): Promise<ExplorationData> => ({
        nodes: [
          { id: "req_main", type: "requirement", priority: "high" },
          { id: "req_dep1", type: "requirement", priority: "medium" }
        ],
        relations: [{ from: "req_main", to: "req_dep1", type: "depends_on" }],
        insights: ["依存要件 req_dep1 が未実装です。先に実装が必要です。"]
      });
      
      const planTasks = createPlanTasksForRequirement(mockExplore);
      const result = await planTasks("req_main");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        // 依存要件のタスクが先に来る
        assertEquals(result.data.tasks[0].targetId, "req_dep1");
        assertEquals(result.data.tasks[1].targetId, "req_main");
      }
    });

    it("test_planTasksForRequirement_circularDependency_returnsError", async () => {
      const mockExplore = async (): Promise<ExplorationData> => ({
        nodes: [
          { id: "req_a", type: "requirement" },
          { id: "req_b", type: "requirement" }
        ],
        relations: [
          { from: "req_a", to: "req_b", type: "depends_on" },
          { from: "req_b", to: "req_a", type: "depends_on" }
        ],
        insights: []
      });
      
      const planTasks = createPlanTasksForRequirement(mockExplore);
      const result = await planTasks("req_a");
      
      assertEquals(result.ok, false);
      if (!result.ok) {
        assertEquals(result.error.type, "circular_dependency");
      }
    });

    it("test_planTasksForRequirement_estimatesTime_sumsTaskTimes", async () => {
      const mockExplore = async (): Promise<ExplorationData> => ({
        nodes: [{ id: "req_1", type: "requirement" }],
        relations: [],
        insights: ["未実装", "テストなし"]
      });
      
      const planTasks = createPlanTasksForRequirement(mockExplore);
      const result = await planTasks("req_1");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        // 実装(120分) + テスト(60分) = 180分
        assertEquals(result.data.totalEstimatedTime, 180);
      }
    });
  });

  describe("planUnimplementedRequirements", () => {
    it("test_planUnimplementedRequirements_groupsByPriority_createsBatchPlans", async () => {
      const mockFindUnimplemented = async () => [
        { id: "req_high1", type: "requirement" as const, priority: "high" },
        { id: "req_high2", type: "requirement" as const, priority: "high" },
        { id: "req_low1", type: "requirement" as const, priority: "low" }
      ];
      
      const planUnimplemented = createPlanUnimplementedRequirements(
        mockFindUnimplemented,
        async () => ({ nodes: [], relations: [], insights: [] })
      );
      const result = await planUnimplemented();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        // 優先度ごとにバッチ計画が作成される
        const highPriorityPlan = result.data.find(p => p.id.includes("high"));
        const lowPriorityPlan = result.data.find(p => p.id.includes("low"));
        assertExists(highPriorityPlan);
        assertExists(lowPriorityPlan);
      }
    });

    it("test_planUnimplementedRequirements_empty_returnsEmptyArray", async () => {
      const mockFindUnimplemented = async () => [];
      
      const planUnimplemented = createPlanUnimplementedRequirements(
        mockFindUnimplemented,
        async () => ({ nodes: [], relations: [], insights: [] })
      );
      const result = await planUnimplemented();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.length, 0);
      }
    });
  });

  describe("planTasksForLocation", () => {
    it("test_planTasksForLocation_hasUnimplementedReqs_createsImplementTasks", async () => {
      const mockExploreLocation = async (): Promise<ExplorationData> => ({
        nodes: [
          { id: "req_1", type: "requirement", title: "Feature 1" },
          { id: "req_2", type: "requirement", title: "Feature 2" }
        ],
        relations: [],
        insights: []
      });
      
      const mockCheckImpl = async (reqId: string) => false; // 全て未実装
      
      const planLocation = createPlanTasksForLocation(mockExploreLocation, mockCheckImpl);
      const result = await planLocation("/src/features");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.tasks.length, 2);
        assertEquals(result.data.tasks.every(t => t.type === "implement"), true);
      }
    });

    it("test_planTasksForLocation_allImplemented_returnsEmptyPlan", async () => {
      const mockExploreLocation = async (): Promise<ExplorationData> => ({
        nodes: [
          { id: "req_1", type: "requirement" },
          { id: "code_1", type: "code" }
        ],
        relations: [],
        insights: []
      });
      
      const mockCheckImpl = async () => true; // 全て実装済み
      
      const planLocation = createPlanTasksForLocation(mockExploreLocation, mockCheckImpl);
      const result = await planLocation("/src/features");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.tasks.length, 0);
      }
    });
  });

  describe("pure functions", () => {
    it("test_orderTasksByDependency_topologicalSort_correctOrder", () => {
      const tasks: PlannedTask[] = [
        {
          id: "task_3",
          type: "implement",
          targetId: "req_3",
          title: "Task 3",
          description: "",
          priority: "medium",
          prerequisites: ["task_1", "task_2"],
          status: "pending"
        },
        {
          id: "task_1",
          type: "implement",
          targetId: "req_1",
          title: "Task 1",
          description: "",
          priority: "high",
          prerequisites: [],
          status: "pending"
        },
        {
          id: "task_2",
          type: "test",
          targetId: "req_2",
          title: "Task 2",
          description: "",
          priority: "medium",
          prerequisites: ["task_1"],
          status: "pending"
        }
      ];
      
      const ordered = orderTasksByDependency(tasks);
      
      assertEquals(ordered[0].id, "task_1");
      assertEquals(ordered[1].id, "task_2");
      assertEquals(ordered[2].id, "task_3");
    });

    it("test_buildDependencyGraph_fromRelations_createsGraph", () => {
      const exploration: ExplorationData = {
        nodes: [
          { id: "req_1", type: "requirement" },
          { id: "req_2", type: "requirement" },
          { id: "req_3", type: "requirement" }
        ],
        relations: [
          { from: "req_1", to: "req_2", type: "depends_on" },
          { from: "req_2", to: "req_3", type: "depends_on" }
        ],
        insights: []
      };
      
      const graph = buildDependencyGraph(exploration);
      
      assertEquals(graph.nodes.length, 3);
      assertEquals(graph.edges.length, 2);
      assertExists(graph.edges.find(e => e.from === "req_1" && e.to === "req_2"));
    });
  });
});

// 規約準拠: 高階関数スタブ（実装はまだない）
declare function createPlanTasksForRequirement(
  explore: (reqId: string) => Promise<ExplorationData>
): PlanTasksForRequirement;

declare function createPlanUnimplementedRequirements(
  findUnimplemented: () => Promise<any[]>,
  explore: (reqId: string) => Promise<ExplorationData>
): PlanUnimplementedRequirements;

declare function createPlanTasksForLocation(
  exploreLocation: (path: string) => Promise<ExplorationData>,
  checkImplementation: (reqId: string) => Promise<boolean>
): PlanTasksForLocation;

// 純粋関数
declare function orderTasksByDependency(tasks: PlannedTask[]): PlannedTask[];
declare function buildDependencyGraph(exploration: ExplorationData): DependencyGraph;