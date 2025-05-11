import React from 'react';
import { VersionProgressBar } from './VersionProgressBar';
import { CompletionTimeline, VersionStatus } from './CompletionTimeline';

interface VersionSummary {
  versionId: string;
  timestamp: string;
  description: string;
  progressPercentage: number;
  totalLocations: number;
  completedLocations: number;
  completionStatus: VersionStatus;
}

interface VersionStats {
  totalVersions: number;
  overallTotalLocations: number;
  overallCompletedLocations: number;
  overallIncompleteLocations: number;
  completionStatusCounts: {
    completed: number;
    in_progress: number;
    not_started: number;
  };
}

interface VersionCompletionDashboardProps {
  versions: VersionSummary[];
  statistics: VersionStats;
  onVersionSelect: (versionId: string) => void;
  onRecalculateAll: () => void;
  selectedVersionId?: string;
  isLoading?: boolean;
}

export function VersionCompletionDashboard({
  versions,
  statistics,
  onVersionSelect,
  onRecalculateAll,
  selectedVersionId,
  isLoading = false
}: VersionCompletionDashboardProps) {
  const overallProgress = statistics.overallTotalLocations > 0
    ? statistics.overallCompletedLocations / statistics.overallTotalLocations
    : 0;

  return (
    <div className="space-y-6">
      {/* Overall Statistics */}
      <div className="bg-white border rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">プロジェクト進捗状況</h2>
          <button
            onClick={onRecalculateAll}
            disabled={isLoading}
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            全バージョンを再計算
          </button>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-sm text-gray-600">総バージョン数</div>
            <div className="text-2xl font-bold">{statistics.totalVersions}</div>
          </div>
          
          <div className="bg-green-50 p-4 rounded">
            <div className="text-sm text-gray-600">完了済み</div>
            <div className="text-2xl font-bold text-green-600">
              {statistics.completionStatusCounts.completed}
            </div>
          </div>
          
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-sm text-gray-600">進行中</div>
            <div className="text-2xl font-bold text-blue-600">
              {statistics.completionStatusCounts.in_progress}
            </div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-sm text-gray-600">未着手</div>
            <div className="text-2xl font-bold text-gray-600">
              {statistics.completionStatusCounts.not_started}
            </div>
          </div>
        </div>
        
        <VersionProgressBar
          versionId="全体"
          progress={overallProgress}
          completedLocations={statistics.overallCompletedLocations}
          totalLocations={statistics.overallTotalLocations}
          className="mt-4"
        />
      </div>

      {/* Version List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Progress Bars List */}
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">バージョン別進捗</h3>
          <div className="space-y-4">
            {versions.map((version) => (
              <div
                key={version.versionId}
                className={`p-3 rounded border cursor-pointer transition-all ${
                  selectedVersionId === version.versionId
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
                onClick={() => onVersionSelect(version.versionId)}
              >
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span className="font-medium">{version.versionId}</span>
                  <span>{version.description}</span>
                </div>
                <VersionProgressBar
                  versionId={version.versionId}
                  progress={version.progressPercentage}
                  completedLocations={version.completedLocations}
                  totalLocations={version.totalLocations}
                />
              </div>
            ))}
            
            {versions.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                バージョンが見つかりません
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">進捗タイムライン</h3>
          <CompletionTimeline
            items={versions.map(v => ({
              versionId: v.versionId,
              timestamp: v.timestamp,
              description: v.description,
              progress: v.progressPercentage,
              status: v.completionStatus
            }))}
          />
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
              <span>処理中...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
