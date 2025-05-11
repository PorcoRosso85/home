import React from 'react';

interface VersionProgressBarProps {
  versionId: string;
  progress: number; // 0.0 to 1.0
  completedLocations: number;
  totalLocations: number;
  className?: string;
}

export function VersionProgressBar({
  versionId,
  progress,
  completedLocations,
  totalLocations,
  className = ''
}: VersionProgressBarProps) {
  const percentage = Math.round(progress * 100);
  
  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between text-sm text-gray-600 mb-1">
        <span>{versionId}</span>
        <span>{completedLocations}/{totalLocations} ({percentage}%)</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-300 ${
            percentage === 100 
              ? 'bg-green-500' 
              : percentage === 0 
              ? 'bg-gray-300' 
              : 'bg-blue-500'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
