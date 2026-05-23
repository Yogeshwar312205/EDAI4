// History Panel Component - Main history view
import React, { useState } from 'react';
import { useHistoryStore } from '@/store/useHistoryStore';
import { useAppStore } from '@/store/useAppStore';
import { HistoryCard } from './HistoryCard';
import type { HistoryEntry } from '@/types/history';
import { History, Search, Trash2, Upload, AlertCircle } from 'lucide-react';

export const HistoryPanel: React.FC = () => {
  const { entries, deleteEntry, clearAll, resolveImageUrl } = useHistoryStore();
  const { setUploadedImage, setProcessingResult, setGraphData, setActiveView } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [loadingEntryId, setLoadingEntryId] = useState<string | null>(null);

  // Filter entries based on search
  const filteredEntries = entries.filter((entry) =>
    entry.imageName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleLoadEntry = async (entry: HistoryEntry) => {
    console.log('[HistoryPanel] Loading entry:', entry.imageName);
    setLoadingEntryId(entry.id);

    try {
      // Fetch the full-size image from IndexedDB; falls back to thumbnail
      const imageUrl = await resolveImageUrl(entry);

      setUploadedImage(imageUrl);
      setProcessingResult(entry.processingResult);
      setGraphData(entry.graphData);

      // Switch to canvas view
      setActiveView('canvas');
      console.log('[HistoryPanel] Entry loaded successfully');
    } catch (error) {
      console.error('[HistoryPanel] Failed to load entry:', error);
    } finally {
      setLoadingEntryId(null);
    }
  };

  const handleClearAll = () => {
    if (showClearConfirm) {
      clearAll();
      setShowClearConfirm(false);
    } else {
      setShowClearConfirm(true);
      // Auto-hide confirmation after 3 seconds
      setTimeout(() => setShowClearConfirm(false), 3000);
    }
  };

  // Empty state
  if (entries.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-industrial-800 rounded-lg border border-industrial-600">
        <div className="text-center p-8 max-w-md">
          <History className="w-16 h-16 text-industrial-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-industrial-100 mb-2">
            No Processing History
          </h2>
          <p className="text-industrial-400 mb-6">
            Upload and process a P&ID to start building your history timeline
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-industrial-500">
            <Upload className="w-4 h-4" />
            <span>Your processed P&IDs will appear here</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-industrial-800 rounded-lg border border-industrial-600">
      {/* Header */}
      <div className="p-4 border-b border-industrial-600">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <History className="w-6 h-6 text-accent-blue" />
            <h2 className="text-xl font-bold text-industrial-100">
              Processing History
            </h2>
            <span className="px-2 py-1 bg-industrial-700 rounded text-sm font-mono text-industrial-300">
              {entries.length}
            </span>
          </div>
          <button
            onClick={handleClearAll}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
              showClearConfirm
                ? 'bg-accent-red text-white hover:bg-red-600'
                : 'bg-industrial-700 text-industrial-300 hover:bg-industrial-600 hover:text-accent-red'
            }`}
          >
            <Trash2 className="w-4 h-4" />
            {showClearConfirm ? 'Confirm Clear All?' : 'Clear All'}
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-industrial-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename..."
            className="w-full pl-10 pr-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 placeholder-industrial-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
          />
        </div>

        {/* Search results info */}
        {searchQuery && (
          <div className="mt-2 text-sm text-industrial-400">
            {filteredEntries.length === 0 ? (
              <div className="flex items-center gap-2 text-industrial-500">
                <AlertCircle className="w-4 h-4" />
                No results found for "{searchQuery}"
              </div>
            ) : (
              <span>
                Showing {filteredEntries.length} of {entries.length} entries
              </span>
            )}
          </div>
        )}
      </div>

      {/* History List */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {filteredEntries.map((entry) => (
          <HistoryCard
            key={entry.id}
            entry={entry}
            onLoad={handleLoadEntry}
            onDelete={deleteEntry}
            isLoading={loadingEntryId === entry.id}
          />
        ))}
      </div>

      {/* Footer Stats */}
      <div className="p-3 border-t border-industrial-600 bg-industrial-900/50">
        <div className="flex gap-4 text-xs text-industrial-400 font-mono">
          <div>
            Total Entries:{' '}
            <span className="text-accent-cyan font-bold">{entries.length}</span>
          </div>
          <div>
            Total Detections:{' '}
            <span className="text-accent-green font-bold">
              {entries.reduce((sum, e) => sum + e.metadata.detectionCount, 0)}
            </span>
          </div>
          <div>
            Total Instruments:{' '}
            <span className="text-accent-yellow font-bold">
              {entries.reduce((sum, e) => sum + e.metadata.instrumentCount, 0)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
