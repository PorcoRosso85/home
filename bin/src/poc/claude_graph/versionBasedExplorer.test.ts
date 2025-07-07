/**
 * VersionBasedExplorer Tests - TDD Red Phase
 * VersionStateを起点としたタスク探索のテスト
 * エンジニアが「次に何をすべきか」を知るための機能
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.210.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.210.0/testing/bdd.ts";

// 規約準拠: Result型
type VersionExploreResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: VersionExploreError };

type VersionExploreError = 
  | { type: "no_active_version"; message: string }
  | { type: "version_not_found"; versionId: string }
  | { type: "database_error"; message: string };

// ドメイン型定義
interface NextTask {
  requirementId: string;
  title: string;
  description?: string;
  priority: 'high' | 'medium' | 'low';
  reason: string; // なぜこのタスクが次なのか
  blockedBy: string[]; // 依存している未完了タスク
  location?: string; // 実装場所のURI
  estimatedEffort?: number; // 推定工数（分）
}

interface VersionContext {
  versionId: string;
  versionDescription: string;
  progressPercentage: number;
  totalRequirements: number;
  completedRequirements: number;
  inProgressRequirements: number;
}

interface WorkPlan {
  currentVersion: VersionContext;
  nextTasks: NextTask[]; // 優先順位順
  blockedTasks: NextTask[]; // 依存関係でブロックされているタスク
  completedRecently: string[]; // 最近完了したタスクID
}

// Cypherクエリ実行型
type CypherQuery = (query: string, params?: Record<string, any>) => Promise<any[]>;

describe("VersionBasedExplorer", () => {
  describe("getCurrentVersion", () => {
    it("test_getCurrentVersion_latestActive_returnsVersionContext", async () => {
      const mockQuery: CypherQuery = async (query) => {
        if (query.includes("VersionState")) {
          return [{
            id: "v2.0",
            description: "認証機能追加",
            timestamp: "2024-01-20T10:00:00Z",
            progress_percentage: 0.6
          }];
        }
        if (query.includes("COUNT")) {
          return [{ total: 10, completed: 6, in_progress: 2 }];
        }
        return [];
      };
      
      const getCurrentVersion = createGetCurrentVersion(mockQuery);
      const result = await getCurrentVersion();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.versionId, "v2.0");
        assertEquals(result.data.progressPercentage, 0.6);
        assertEquals(result.data.totalRequirements, 10);
        assertEquals(result.data.completedRequirements, 6);
      }
    });

    it("test_getCurrentVersion_noActiveVersion_returnsError", async () => {
      const mockQuery: CypherQuery = async () => [];
      
      const getCurrentVersion = createGetCurrentVersion(mockQuery);
      const result = await getCurrentVersion();
      
      assertEquals(result.ok, false);
      if (!result.ok) {
        assertEquals(result.error.type, "no_active_version");
      }
    });
  });

  describe("getNextTask", () => {
    it("test_getNextTask_highPriorityUnimplemented_returnsTask", async () => {
      const mockQuery: CypherQuery = async (query) => {
        // 現在のバージョンで追跡される未実装要件を返す
        return [{
          req_id: "req_auth_api",
          req_title: "認証API実装",
          req_description: "RESTful認証エンドポイント",
          req_priority: "high",
          location_uri: "/src/api/auth",
          has_dependencies: false
        }];
      };
      
      const getNextTask = createGetNextTask(mockQuery);
      const result = await getNextTask("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.requirementId, "req_auth_api");
        assertEquals(result.data.priority, "high");
        assertEquals(result.data.reason, "最優先度の未実装要件");
        assertEquals(result.data.blockedBy.length, 0);
      }
    });

    it("test_getNextTask_withUnmetDependencies_returnsBlockedInfo", async () => {
      const mockQuery: CypherQuery = async (query) => {
        if (query.includes("DEPENDS_ON")) {
          return [{
            req_id: "req_oauth",
            req_title: "OAuth統合",
            req_priority: "high",
            blocked_by: ["req_user_model", "req_session_store"],
            location_uri: "/src/auth/oauth"
          }];
        }
        return [];
      };
      
      const getNextTask = createGetNextTask(mockQuery);
      const result = await getNextTask("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.requirementId, "req_oauth");
        assertEquals(result.data.blockedBy.length, 2);
        assertExists(result.data.reason.includes("依存"));
      }
    });

    it("test_getNextTask_allTasksCompleted_returnsNull", async () => {
      const mockQuery: CypherQuery = async () => [];
      
      const getNextTask = createGetNextTask(mockQuery);
      const result = await getNextTask("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data, null); // 全タスク完了
      }
    });
  });

  describe("getWorkPlan", () => {
    it("test_getWorkPlan_fullContext_returnsCompletePlan", async () => {
      const mockQuery: CypherQuery = async (query) => {
        if (query.includes("VersionState")) {
          return [{
            id: "v2.0",
            description: "認証機能",
            progress_percentage: 0.4
          }];
        }
        if (query.includes("NOT EXISTS") && query.includes("IS_IMPLEMENTED_BY")) {
          // 未実装タスク
          return [
            { req_id: "req_1", title: "基本認証", priority: "high" },
            { req_id: "req_2", title: "セッション管理", priority: "high" },
            { req_id: "req_3", title: "ログ記録", priority: "medium" }
          ];
        }
        if (query.includes("recently_completed")) {
          return [
            { req_id: "req_user_model", completed_at: "2024-01-19" }
          ];
        }
        return [];
      };
      
      const getWorkPlan = createGetWorkPlan(mockQuery);
      const result = await getWorkPlan();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.currentVersion.versionId, "v2.0");
        assertEquals(result.data.nextTasks.length, 3);
        assertEquals(result.data.nextTasks[0].priority, "high");
        assertExists(result.data.completedRecently.includes("req_user_model"));
      }
    });

    it("test_getWorkPlan_withBlockedTasks_separatesBlockedFromReady", async () => {
      const mockQuery: CypherQuery = async (query) => {
        if (query.includes("blocked_tasks")) {
          return [
            { 
              req_id: "req_advanced_auth",
              title: "高度な認証",
              priority: "high",
              blocked_by: ["req_basic_auth"]
            }
          ];
        }
        if (query.includes("ready_tasks")) {
          return [
            { req_id: "req_basic_auth", title: "基本認証", priority: "high" }
          ];
        }
        return [];
      };
      
      const getWorkPlan = createGetWorkPlan(mockQuery);
      const result = await getWorkPlan();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.nextTasks.length, 1);
        assertEquals(result.data.blockedTasks.length, 1);
        assertEquals(result.data.blockedTasks[0].requirementId, "req_advanced_auth");
      }
    });
  });

  describe("explainWhyThisTask", () => {
    it("test_explainWhyThisTask_providesContext_returnsExplanation", async () => {
      const mockQuery: CypherQuery = async () => [{
        requirement: { id: "req_auth", priority: "high" },
        dependencies: [],
        dependents: ["req_user_dashboard", "req_api_gateway"],
        version_context: "v2.0 - 認証機能実装フェーズ"
      }];
      
      const explainTask = createExplainWhyThisTask(mockQuery);
      const explanation = await explainTask("req_auth");
      
      assertExists(explanation.includes("優先度: high"));
      assertExists(explanation.includes("2つの要件がこのタスクに依存"));
      assertExists(explanation.includes("v2.0"));
    });
  });

  describe("suggestTaskOrder", () => {
    it("test_suggestTaskOrder_considersDependencies_returnsOptimalOrder", async () => {
      const mockQuery: CypherQuery = async () => [{
        tasks: [
          { id: "req_a", priority: "low", depends_on: [] },
          { id: "req_b", priority: "high", depends_on: ["req_a"] },
          { id: "req_c", priority: "medium", depends_on: [] }
        ]
      }];
      
      const suggestOrder = createSuggestTaskOrder(mockQuery);
      const result = await suggestOrder("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        // req_aが先（req_bの依存）、次にreq_c（独立・中優先）、最後にreq_b
        assertEquals(result.data[0].requirementId, "req_a");
        assertEquals(result.data[1].requirementId, "req_c");
        assertEquals(result.data[2].requirementId, "req_b");
      }
    });
  });
});

// Cypherクエリ例（ドキュメント用）
const exampleQueries = {
  // 現在のバージョンの未実装要件を探す
  findUnimplementedInVersion: `
    MATCH (vs:VersionState)
    WHERE vs.progress_percentage < 1.0
    WITH vs ORDER BY vs.timestamp DESC LIMIT 1
    MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
    -[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
    WHERE NOT EXISTS {
      MATCH (r)-[:IS_IMPLEMENTED_BY]->()
    }
    RETURN r, loc.id as location_uri, vs.description as version_context
    ORDER BY 
      CASE r.priority 
        WHEN 'high' THEN 1 
        WHEN 'medium' THEN 2 
        WHEN 'low' THEN 3 
      END,
      r.id
  `,
  
  // 依存関係を考慮したタスク順序
  findTasksWithDependencies: `
    MATCH (r:RequirementEntity)
    WHERE NOT EXISTS { (r)-[:IS_IMPLEMENTED_BY]->() }
    OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
    WHERE NOT EXISTS { (dep)-[:IS_IMPLEMENTED_BY]->() }
    WITH r, collect(dep.id) as blocked_by
    RETURN r.id, r.title, r.priority, blocked_by
    ORDER BY size(blocked_by), r.priority
  `
};

// 高階関数スタブ（実装はまだない）
declare function createGetCurrentVersion(query: CypherQuery): 
  () => Promise<VersionExploreResult<VersionContext>>;

declare function createGetNextTask(query: CypherQuery): 
  (versionId: string) => Promise<VersionExploreResult<NextTask | null>>;

declare function createGetWorkPlan(query: CypherQuery): 
  () => Promise<VersionExploreResult<WorkPlan>>;

declare function createExplainWhyThisTask(query: CypherQuery): 
  (requirementId: string) => Promise<string>;

declare function createSuggestTaskOrder(query: CypherQuery): 
  (versionId: string) => Promise<VersionExploreResult<NextTask[]>>;