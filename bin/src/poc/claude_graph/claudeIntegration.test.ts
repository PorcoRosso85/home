/**
 * ClaudeIntegration Tests - TDD Red Phase
 * 規約準拠: 状態を持たない関数設計、Result型、モジュール分離
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.210.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.210.0/testing/bdd.ts";

// 規約準拠: ドメイン型定義
interface ClaudeInsight {
  type: 'recommendation' | 'warning' | 'info';
  message: string;
  relatedEntities: string[];
  suggestedActions: string[];
}

interface UnderstandResult {
  interpretation: string;
  plans: Array<{ id: string; tasks: any[] }>;
  insights: ClaudeInsight[];
}

interface ProjectState {
  totalRequirements: number;
  implementedRequirements: number;
  testedRequirements: number;
  activePlans: number;
  completedTasks: number;
}

// 規約準拠: Result型
type ClaudeResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: ClaudeError };

type ClaudeError = 
  | { type: "parse_error"; message: string }
  | { type: "planning_failed"; message: string }
  | { type: "state_error"; message: string };

// 規約準拠: 関数型インターフェース（状態を持たない）
type UnderstandAndPlan = (
  naturalLanguageRequest: string,
  currentState: ProjectState
) => Promise<ClaudeResult<UnderstandResult>>;

type SuggestNextActions = (
  projectState: ProjectState
) => Promise<ClaudeResult<ClaudeInsight[]>>;

type ExplainCurrentState = (
  projectState: ProjectState
) => string;

// 依存する関数の型
type ExtractRequirementIds = (text: string) => string[];
type ExtractKeywords = (text: string) => string[];
type SearchRequirements = (keywords: string[]) => Promise<Array<{ id: string; title: string }>>;

describe("ClaudeIntegration", () => {
  describe("understandAndPlan", () => {
    it("test_understandAndPlan_withRequirementId_createsDirectPlan", async () => {
      const mockExtractIds: ExtractRequirementIds = (text) => ["req_user_auth"];
      const mockExtractKeywords: ExtractKeywords = () => [];
      const mockSearch: SearchRequirements = async () => [];
      const mockPlan = async () => ({
        id: "plan_req_user_auth",
        tasks: [{ id: "task_1", type: "implement" }]
      });
      
      const understand = createUnderstandAndPlan(
        mockExtractIds,
        mockExtractKeywords,
        mockSearch,
        mockPlan
      );
      
      const result = await understand(
        "req_user_auth の実装とテストを計画してください",
        { totalRequirements: 10, implementedRequirements: 5, testedRequirements: 3, activePlans: 0, completedTasks: 0 }
      );
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.plans.length, 1);
        assertExists(result.data.interpretation.includes("req_user_auth"));
      }
    });

    it("test_understandAndPlan_withKeywords_searchesRequirements", async () => {
      const mockExtractIds: ExtractRequirementIds = () => [];
      const mockExtractKeywords: ExtractKeywords = (text) => ["認証", "セキュリティ"];
      const mockSearch: SearchRequirements = async (keywords) => [
        { id: "req_auth_1", title: "Basic Authentication" },
        { id: "req_auth_2", title: "OAuth Integration" }
      ];
      const mockPlan = async () => ({ id: "plan_1", tasks: [] });
      
      const understand = createUnderstandAndPlan(
        mockExtractIds,
        mockExtractKeywords,
        mockSearch,
        mockPlan
      );
      
      const result = await understand(
        "認証とセキュリティに関する要件を探して実装計画を作成",
        { totalRequirements: 10, implementedRequirements: 5, testedRequirements: 3, activePlans: 0, completedTasks: 0 }
      );
      
      assertEquals(result.ok, true);
      if (result.ok) {
        const infoInsight = result.data.insights.find(i => i.type === "info");
        assertExists(infoInsight);
        assertEquals(infoInsight?.relatedEntities.length, 2);
      }
    });

    it("test_understandAndPlan_invalidRequest_returnsParseError", async () => {
      const mockExtractIds: ExtractRequirementIds = () => [];
      const mockExtractKeywords: ExtractKeywords = () => [];
      const mockSearch: SearchRequirements = async () => [];
      const mockPlan = async () => { throw new Error("No requirements found"); };
      
      const understand = createUnderstandAndPlan(
        mockExtractIds,
        mockExtractKeywords,
        mockSearch,
        mockPlan
      );
      
      const result = await understand(
        "",
        { totalRequirements: 0, implementedRequirements: 0, testedRequirements: 0, activePlans: 0, completedTasks: 0 }
      );
      
      assertEquals(result.ok, false);
      if (!result.ok) {
        assertEquals(result.error.type, "parse_error");
      }
    });

    it("test_understandAndPlan_multipleRequirements_createsMultiplePlans", async () => {
      const mockExtractIds: ExtractRequirementIds = () => ["req_1", "req_2", "req_3"];
      const mockExtractKeywords: ExtractKeywords = () => [];
      const mockSearch: SearchRequirements = async () => [];
      let planCount = 0;
      const mockPlan = async (reqId: string) => ({
        id: `plan_${reqId}_${++planCount}`,
        tasks: [{ id: `task_${planCount}`, type: "implement" }]
      });
      
      const understand = createUnderstandAndPlan(
        mockExtractIds,
        mockExtractKeywords,
        mockSearch,
        mockPlan
      );
      
      const result = await understand(
        "req_1, req_2, req_3 を実装して",
        { totalRequirements: 10, implementedRequirements: 5, testedRequirements: 3, activePlans: 0, completedTasks: 0 }
      );
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.plans.length, 3);
      }
    });
  });

  describe("suggestNextActions", () => {
    it("test_suggestNextActions_lowImplementation_suggestsImplementation", async () => {
      const mockFindUnimplemented = async () => [
        { id: "req_1", priority: "high" },
        { id: "req_2", priority: "high" },
        { id: "req_3", priority: "medium" }
      ];
      const mockFindUntested = async () => [];
      
      const suggest = createSuggestNextActions(mockFindUnimplemented, mockFindUntested);
      const result = await suggest({
        totalRequirements: 10,
        implementedRequirements: 3,  // 30% - 低い
        testedRequirements: 3,
        activePlans: 0,
        completedTasks: 0
      });
      
      assertEquals(result.ok, true);
      if (result.ok) {
        const implRecommendation = result.data.find(i => 
          i.type === "recommendation" && i.message.includes("未実装")
        );
        assertExists(implRecommendation);
        assertEquals(implRecommendation?.suggestedActions.includes("高優先度の要件から実装開始"), true);
      }
    });

    it("test_suggestNextActions_lowTestCoverage_suggestsTests", async () => {
      const mockFindUnimplemented = async () => [];
      const mockFindUntested = async () => [
        { id: "req_payment", priority: "high" },
        { id: "req_user", priority: "high" }
      ];
      
      const suggest = createSuggestNextActions(mockFindUnimplemented, mockFindUntested);
      const result = await suggest({
        totalRequirements: 10,
        implementedRequirements: 8,
        testedRequirements: 2,  // 20% - 低い
        activePlans: 0,
        completedTasks: 0
      });
      
      assertEquals(result.ok, true);
      if (result.ok) {
        const testWarning = result.data.find(i => 
          i.type === "warning" && i.message.includes("テスト")
        );
        assertExists(testWarning);
      }
    });

    it("test_suggestNextActions_goodProgress_minimalSuggestions", async () => {
      const mockFindUnimplemented = async () => [];
      const mockFindUntested = async () => [];
      
      const suggest = createSuggestNextActions(mockFindUnimplemented, mockFindUntested);
      const result = await suggest({
        totalRequirements: 10,
        implementedRequirements: 9,  // 90% - 高い
        testedRequirements: 8,       // 80% - 高い
        activePlans: 2,
        completedTasks: 15
      });
      
      assertEquals(result.ok, true);
      if (result.ok) {
        assertEquals(result.data.length, 0);  // 問題なければ提案なし
      }
    });
  });

  describe("explainCurrentState", () => {
    it("test_explainCurrentState_generatesMarkdown_withStats", () => {
      const explain = createExplainCurrentState();
      const state: ProjectState = {
        totalRequirements: 45,
        implementedRequirements: 28,
        testedRequirements: 22,
        activePlans: 3,
        completedTasks: 15
      };
      
      const explanation = explain(state);
      
      assertExists(explanation.includes("## 現在のプロジェクト状態"));
      assertExists(explanation.includes("総要件数: 45"));
      assertExists(explanation.includes("実装済み: 28 (62.2%)"));
      assertExists(explanation.includes("テスト済み: 22 (48.9%)"));
    });

    it("test_explainCurrentState_zeroRequirements_handlesGracefully", () => {
      const explain = createExplainCurrentState();
      const state: ProjectState = {
        totalRequirements: 0,
        implementedRequirements: 0,
        testedRequirements: 0,
        activePlans: 0,
        completedTasks: 0
      };
      
      const explanation = explain(state);
      
      assertExists(explanation.includes("総要件数: 0"));
      // ゼロ除算を避ける
      assertExists(!explanation.includes("NaN"));
    });
  });

  describe("pure utility functions", () => {
    it("test_extractRequirementIds_findsValidIds", () => {
      const extract = createExtractRequirementIds();
      const text = "req_user_auth と req_payment_process を実装して、req_123 も忘れずに";
      
      const ids = extract(text);
      
      assertEquals(ids.length, 3);
      assertEquals(ids.includes("req_user_auth"), true);
      assertEquals(ids.includes("req_payment_process"), true);
      assertEquals(ids.includes("req_123"), true);
    });

    it("test_extractKeywords_filtersStopWords", () => {
      const extract = createExtractKeywords();
      const text = "認証システムの実装を計画してください";
      
      const keywords = extract(text);
      
      assertEquals(keywords.includes("の"), false);  // ストップワード
      assertEquals(keywords.includes("を"), false);  // ストップワード
      assertEquals(keywords.includes("認証システム"), true);
      assertEquals(keywords.includes("実装"), true);
      assertEquals(keywords.includes("計画"), true);
    });

    it("test_interpretRequest_generatesProperMessage", () => {
      const interpret = createInterpretRequest();
      
      const message1 = interpret("何か作業して", ["req_1", "req_2"], []);
      assertExists(message1.includes("要件ID: req_1, req_2"));
      
      const message2 = interpret("認証を実装", [], ["認証", "実装"]);
      assertExists(message2.includes("キーワード: 認証, 実装"));
      
      const message3 = interpret("req_1の認証", ["req_1"], ["認証"]);
      assertExists(message3.includes("要件ID: req_1"));
      assertExists(message3.includes("キーワード: 認証"));
    });
  });
});

// 規約準拠: 高階関数スタブ（実装はまだない）
declare function createUnderstandAndPlan(
  extractIds: ExtractRequirementIds,
  extractKeywords: ExtractKeywords,
  searchRequirements: SearchRequirements,
  planTasks: (reqId: string) => Promise<any>
): UnderstandAndPlan;

declare function createSuggestNextActions(
  findUnimplemented: () => Promise<any[]>,
  findUntested: () => Promise<any[]>
): SuggestNextActions;

declare function createExplainCurrentState(): ExplainCurrentState;

// 純粋関数
declare function createExtractRequirementIds(): ExtractRequirementIds;
declare function createExtractKeywords(): ExtractKeywords;
declare function createInterpretRequest(): (
  request: string,
  requirementIds: string[],
  keywords: string[]
) => string;