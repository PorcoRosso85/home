/**
 * TaskExplorer Tests - TDD Red Phase
 * 規約準拠: 関数レベルテスト、Result型使用、エラーハンドリング
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.210.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.210.0/testing/bdd.ts";
import { 
  createExploreFromRequirement, 
  createFindUnimplementedRequirements,
  createExploreByLocationURI
} from "./taskExplorer.ts";

// 規約準拠: Result型定義
type ExploreResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: ExploreError };

type ExploreError = 
  | { type: "requirement_not_found"; requirementId: string }
  | { type: "database_error"; message: string }
  | { type: "invalid_input"; message: string };

// 規約準拠: ドメイン型定義（DBに依存しない）
interface TaskNode {
  id: string;
  type: 'requirement' | 'code' | 'test';
  title?: string;
  description?: string;
  priority?: string;
  status?: 'pending' | 'implemented' | 'tested';
}

interface TaskRelation {
  from: string;
  to: string;
  type: 'implements' | 'verifies' | 'depends_on';
}

interface ExplorationData {
  nodes: TaskNode[];
  relations: TaskRelation[];
  insights: string[];
}

// 規約準拠: 関数インターフェース（高階関数でDI）
type ExploreFromRequirement = (
  requirementId: string
) => Promise<ExploreResult<ExplorationData>>;

type FindUnimplementedRequirements = () => Promise<ExploreResult<TaskNode[]>>;

type FindUntestedRequirements = () => Promise<ExploreResult<TaskNode[]>>;

type ExploreByLocationURI = (
  uriPath: string
) => Promise<ExploreResult<ExplorationData>>;

// モックデータベースクエリ関数
type DatabaseQuery = (query: string, params?: Record<string, any>) => Promise<any[]>;

describe("TaskExplorer", () => {
  describe("exploreFromRequirement", () => {
    it("test_exploreFromRequirement_validId_returnsRequirementData", async () => {
      // この関数はまだ実装されていないため、テストは失敗する
      const mockQuery: DatabaseQuery = async () => [{
        r: { id: "req_user_auth", title: "User Authentication", description: "認証機能", priority: "high" },
        implementations: [],
        tests: [],
        dependencies: []
      }];
      const exploreFromRequirement = createExploreFromRequirement(mockQuery);
      
      const result = await exploreFromRequirement("req_user_auth");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertExists(result.data.nodes.find(n => n.id === "req_user_auth"));
        assertEquals(result.data.nodes[0].type, "requirement");
      }
    });

    it("test_exploreFromRequirement_nonExistentId_returnsNotFoundError", async () => {
      const mockQuery: DatabaseQuery = async () => [];
      const exploreFromRequirement = createExploreFromRequirement(mockQuery);
      
      const result = await exploreFromRequirement("req_not_exists");
      
      assertEquals(result.ok, false);
      if (!result.ok) {
        assertEquals(result.error.type, "requirement_not_found");
      }
    });

    it("test_exploreFromRequirement_withImplementation_includesCodeNodes", async () => {
      const mockQuery: DatabaseQuery = async () => [{
        r: { id: "req_user_auth", title: "User Authentication", description: "認証機能", priority: "high" },
        implementations: [{ persistent_id: "code_123", name: "UserAuth", type: "class" }],
        tests: [],
        dependencies: []
      }];
      const exploreFromRequirement = createExploreFromRequirement(mockQuery);
      
      const result = await exploreFromRequirement("req_user_auth");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertExists(result.data.nodes.find(n => n.id === "code_123" && n.type === "code"));
        assertExists(result.data.relations.find(r => r.type === "implements"));
      }
    });

    it("test_exploreFromRequirement_withoutImplementation_generatesInsight", async () => {
      const mockQuery: DatabaseQuery = async () => [{
        r: { id: "req_user_auth", title: "User Authentication", description: "認証機能", priority: "high" },
        implementations: [],
        tests: [],
        dependencies: []
      }];
      const exploreFromRequirement = createExploreFromRequirement(mockQuery);
      
      const result = await exploreFromRequirement("req_user_auth");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertExists(result.data.insights.find(i => i.includes("未実装")));
      }
    });

    it("test_exploreFromRequirement_databaseError_returnsError", async () => {
      const mockQuery: DatabaseQuery = async () => {
        throw new Error("Connection failed");
      };
      const exploreFromRequirement = createExploreFromRequirement(mockQuery);
      
      const result = await exploreFromRequirement("req_user_auth");
      
      assertEquals(result.ok, false);
      if (!result.ok) {
        assertEquals(result.error.type, "database_error");
      }
    });
  });

  describe("findUnimplementedRequirements", () => {
    it("test_findUnimplementedRequirements_hasUnimplemented_returnsRequirements", async () => {
      const mockQuery: DatabaseQuery = async () => [
        { id: "req_1", title: "Requirement 1", priority: "high" },
        { id: "req_2", title: "Requirement 2", priority: "medium" }
      ];
      const findUnimplemented = createFindUnimplementedRequirements(mockQuery);
      
      const result = await findUnimplemented();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.length, 2);
        assertEquals(result.data[0].status, "pending");
      }
    });

    it("test_findUnimplementedRequirements_allImplemented_returnsEmpty", async () => {
      const mockQuery: DatabaseQuery = async () => [];
      const findUnimplemented = createFindUnimplementedRequirements(mockQuery);
      
      const result = await findUnimplemented();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.length, 0);
      }
    });

    it("test_findUnimplementedRequirements_sortedByPriority_highFirst", async () => {
      const mockQuery: DatabaseQuery = async () => [
        { id: "req_low", title: "Low Priority", priority: "low" },
        { id: "req_high", title: "High Priority", priority: "high" },
        { id: "req_medium", title: "Medium Priority", priority: "medium" }
      ];
      const findUnimplemented = createFindUnimplementedRequirements(mockQuery);
      
      const result = await findUnimplemented();
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data[0].priority, "high");
        assertEquals(result.data[1].priority, "medium");
        assertEquals(result.data[2].priority, "low");
      }
    });
  });

  describe("exploreByLocationURI", () => {
    it("test_exploreByLocationURI_validPath_returnsRelatedEntities", async () => {
      const mockQuery: DatabaseQuery = async () => [
        { 
          location: "/src/services/user",
          requirement_id: "req_user", 
          title: "User Management", 
          priority: "high",
          is_implemented: false,
          has_tests: false
        }
      ];
      const exploreByLocation = createExploreByLocationURI(mockQuery);
      
      const result = await exploreByLocation("/src/services/user");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.nodes.length, 1);
        assertExists(result.data.nodes.find(n => n.type === "requirement"));
        assertEquals(result.data.insights.length, 2); // 未実装とテストなしの警告
      }
    });

    it("test_exploreByLocationURI_noEntities_returnsEmptyWithInsight", async () => {
      const mockQuery: DatabaseQuery = async () => [];
      const exploreByLocation = createExploreByLocationURI(mockQuery);
      
      const result = await exploreByLocation("/src/unknown/path");
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.nodes.length, 0);
        assertExists(result.data.insights.find(i => i.includes("見つかりません")));
      }
    });
  });
});

