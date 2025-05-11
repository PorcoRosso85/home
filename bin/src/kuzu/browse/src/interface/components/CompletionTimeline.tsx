import React from 'react';

export type VersionStatus = 'completed' | 'in_progress' | 'not_started';

interface TimelineItem {
  versionId: string;
  timestamp: string;
  description: string;
  progress: number;
  status: VersionStatus;
}

interface CompletionTimelineProps {
  items: TimelineItem[];
  className?: string;
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getStatusColor(status: VersionStatus): string {
  switch (status) {
    case 'completed':
      return 'border-green-400 bg-green-50';
    case 'in_progress':
      return 'border-blue-400 bg-blue-50';
    case 'not_started':
      return 'border-gray-400 bg-gray-50';
    default:
      return 'border-gray-400 bg-gray-50';
  }
}

function getStatusIcon(status: VersionStatus): React.ReactNode {
  switch (status) {
    case 'completed':
      return (
        <div className="w-3 h-3 bg-green-400 rounded-full border-2 border-white" />
      );
    case 'in_progress':
      return (
        <div className="w-3 h-3 bg-blue-400 rounded-full border-2 border-white animate-pulse" />
      );
    case 'not_started':
      return (
        <div className="w-3 h-3 bg-gray-400 rounded-full border-2 border-white" />
      );
    default:
      return null;
  }
}

export function CompletionTimeline({ items, className = '' }: CompletionTimelineProps) {
  return (
    <div className={`relative ${className}`}>
      {/* Timeline line */}
      <div className="absolute left-5 top-3 bottom-0 w-0.5 bg-gray-200" />
      
      {/* Timeline items */}
      <div className="space-y-6">
        {items.map((item, index) => (
          <div key={item.versionId} className="relative">
            {/* Icon */}
            <div className="absolute left-3 top-1">
              {getStatusIcon(item.status)}
            </div>
            
            {/* Content */}
            <div className={`ml-12 p-4 rounded-lg border ${getStatusColor(item.status)}`}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-gray-900">{item.versionId}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                </div>
                <span className="text-xs text-gray-500">
                  {formatDate(item.timestamp)}
                </span>
              </div>
              
              {/* Progress bar */}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>進捗率</span>
                  <span>{Math.round(item.progress * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      item.status === 'completed' 
                        ? 'bg-green-400' 
                        : item.status === 'in_progress' 
                        ? 'bg-blue-400' 
                        : 'bg-gray-300'
                    }`}
                    style={{ width: `${item.progress * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
