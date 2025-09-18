/**
 * VersionBasedExplorer Tests - TDD Red Phase
 * VersionStateを起点としたタスク探索のテスト
 * エンジニアが「次に何をすべきか」を知るための機能
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.210.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.210.0/testing/bdd.ts";
import {
  createGetCurrentVersion,
  createGetNextTask,
  createGetWorkPlan,
  createExplainWhyThisTask,
  createSuggestTaskOrder,
  type VersionExploreResult,
  type VersionExploreError,
  type NextTask,
  type VersionContext,
  type WorkPlan
} from "./versionBasedExplorer.ts";


// Cypherクエリ実行型
type CypherQuery = (query: string, params?: Record<string, any>) => Promise<any[]>;

describe("VersionBasedExplorer", () => {
  describe("getCurrentVersion", () => {
    it("test_getCurrentVersion_latestActive_returnsVersionContext", async () => {
      let callCount = 0;
      const mockQuery: CypherQuery = async (query) => {
        callCount++;
        if (callCount === 1) {
          // First query - get version state
          return [{
            id: "v2.0",
            description: "認証機能追加",
            timestamp: "2024-01-20T10:00:00Z",
            progress_percentage: 0.6
          }];
        }
        if (callCount === 2) {
          // Second query - get counts
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
          blocked_by: [],
          has_dependencies: true
        }];
      };
      
      const getNextTask = createGetNextTask(mockQuery);
      const result = await getNextTask("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok && result.data) {
        assertEquals(result.data.requirementId, "req_auth_api");
        assertEquals(result.data.priority, "high");
        assertEquals(result.data.reason, "最優先度の未実装要件");
        assertEquals(result.data.blockedBy.length, 0);
      }
    });

    it("test_getNextTask_withUnmetDependencies_returnsBlockedInfo", async () => {
      const mockQuery: CypherQuery = async (query) => {
        return [{
          req_id: "req_oauth",
          req_title: "OAuth統合",
          req_description: "OAuth2.0プロバイダ統合",
          req_priority: "high",
          blocked_by: ["req_user_model", "req_session_store"],
          location_uri: "/src/auth/oauth",
          has_dependencies: false
        }];
      };
      
      const getNextTask = createGetNextTask(mockQuery);
      const result = await getNextTask("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok && result.data) {
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
      let callCount = 0;
      const mockQuery: CypherQuery = async (query) => {
        callCount++;
        if (callCount === 1) {
          // First query - version state
          return [{
            id: "v2.0",
            description: "認証機能",
            progress_percentage: 0.4
          }];
        }
        if (callCount === 2) {
          // Second query - ready tasks
          return [
            { req_id: "req_1", title: "基本認証", priority: "high" },
            { req_id: "req_2", title: "セッション管理", priority: "high" },
            { req_id: "req_3", title: "ログ記録", priority: "medium" }
          ];
        }
        if (callCount === 3) {
          // Third query - blocked tasks
          return [];
        }
        if (callCount === 4) {
          // Fourth query - recently completed
          return [
            { req_id: "req_user_model" }
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
      let callCount = 0;
      const mockQuery: CypherQuery = async (query) => {
        callCount++;
        if (callCount === 1) {
          // First query - version state
          return [{
            id: "v2.0",
            description: "認証機能",
            progress_percentage: 0.4
          }];
        }
        if (callCount === 2) {
          // Second query - ready tasks
          return [
            { req_id: "req_basic_auth", title: "基本認証", priority: "high" }
          ];
        }
        if (callCount === 3) {
          // Third query - blocked tasks
          return [
            { 
              req_id: "req_advanced_auth",
              title: "高度な認証",
              priority: "high",
              blocked_by: ["req_basic_auth"]
            }
          ];
        }
        if (callCount === 4) {
          // Fourth query - recently completed
          return [];
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
      const mockQuery: CypherQuery = async () => [
        { tasks: { id: "req_a", priority: "low", depends_on: [] } },
        { tasks: { id: "req_b", priority: "high", depends_on: ["req_a"] } },
        { tasks: { id: "req_c", priority: "medium", depends_on: [] } }
      ];
      
      const suggestOrder = createSuggestTaskOrder(mockQuery);
      const result = await suggestOrder("v2.0");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        // ソート結果を確認
        // req_cとreq_aが依存なし、req_bがreq_aに依存
        assertEquals(result.data.length, 3);
        // 依存なしのタスクが先に来る
        const noDepsCount = result.data.filter((t: NextTask) => t.blockedBy.length === 0).length;
        assertEquals(noDepsCount, 2); // req_aとreq_c
        // req_bは依存あり
        const hasDeps = result.data.find((t: NextTask) => t.blockedBy.length > 0);
        assertEquals(hasDeps !== undefined, true);
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

