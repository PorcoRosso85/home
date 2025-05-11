import React, { useState, useEffect } from 'react';

interface LocationURI {
  uri_id: string;
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
  completed: boolean;
}

interface LocationCompletionListProps {
  versionId: string;
  locations: LocationURI[];
  onToggleCompletion: (uriId: string, completed: boolean) => void;
  onBatchUpdate: (updates: Array<{ uriId: string; completed: boolean }>) => void;
  className?: string;
}

export function LocationCompletionList({
  versionId,
  locations,
  onToggleCompletion,
  onBatchUpdate,
  className = ''
}: LocationCompletionListProps) {
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'completed' | 'incomplete'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLocations = locations.filter(location => {
    const matchesFilter = 
      filter === 'all' ||
      (filter === 'completed' && location.completed) ||
      (filter === 'incomplete' && !location.completed);
    
    const matchesSearch = 
      location.uri_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      location.path.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  const completedCount = locations.filter(l => l.completed).length;
  const totalCount = locations.length;
  const completionPercentage = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  function handleSelectAll() {
    if (selectedItems.size === filteredLocations.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(filteredLocations.map(l => l.uri_id)));
    }
  }

  function handleItemSelect(uriId: string) {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(uriId)) {
      newSelected.delete(uriId);
    } else {
      newSelected.add(uriId);
    }
    setSelectedItems(newSelected);
  }

  function handleBatchComplete(completed: boolean) {
    const updates = Array.from(selectedItems).map(uriId => ({
      uriId,
      completed
    }));
    onBatchUpdate(updates);
    setSelectedItems(new Set());
  }

  return (
    <div className={`bg-white border rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-semibold">LocationURI 一覧</h3>
          <span className="text-sm text-gray-600">
            {versionId} - {completedCount}/{totalCount} 完了 ({completionPercentage}%)
          </span>
        </div>
        
        {/* Controls */}
        <div className="flex gap-4 flex-wrap">
          <input
            type="text"
            placeholder="URI を検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border rounded flex-1 min-w-0"
          />
          
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as 'all' | 'completed' | 'incomplete')}
            className="px-3 py-2 border rounded"
          >
            <option value="all">全て</option>
            <option value="completed">完了済み</option>
            <option value="incomplete">未完了</option>
          </select>
          
          {selectedItems.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={() => handleBatchComplete(true)}
                className="px-3 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600"
              >
                選択済みを完了
              </button>
              <button
                onClick={() => handleBatchComplete(false)}
                className="px-3 py-2 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                選択済みを未完了
              </button>
            </div>
          )}
        </div>
      </div>

      {/* List */}
      <div className="divide-y">
        {/* Select all header */}
        <div className="flex items-center gap-3 p-2 border-b bg-gray-50">
          <input
            type="checkbox"
            checked={selectedItems.size === filteredLocations.length && filteredLocations.length > 0}
            onChange={handleSelectAll}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-600">
            {selectedItems.size} 選択中
          </span>
        </div>
        
        {/* Items */}
        <div className="max-h-96 overflow-y-auto">
          {filteredLocations.map((location) => (
            <div key={location.uri_id} className="flex items-center gap-3 p-3 hover:bg-gray-50">
              <input
                type="checkbox"
                checked={selectedItems.has(location.uri_id)}
                onChange={() => handleItemSelect(location.uri_id)}
                className="w-4 h-4"
              />
              
              <input
                type="checkbox"
                checked={location.completed}
                onChange={(e) => onToggleCompletion(location.uri_id, e.target.checked)}
                className="w-4 h-4"
                title="完了状態を切り替え"
              />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {location.scheme}://{location.authority}{location.path}
                  </span>
                  {(location.fragment || location.query) && (
                    <span className="text-xs text-gray-500">
                      {location.fragment && `#${location.fragment}`}
                      {location.query && `?${location.query}`}
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-400 truncate">
                  {location.uri_id}
                </div>
              </div>
              
              <span className={`px-2 py-1 text-xs rounded ${
                location.completed 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {location.completed ? '完了' : '未完了'}
              </span>
            </div>
          ))}
          
          {filteredLocations.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              表示する項目がありません
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
