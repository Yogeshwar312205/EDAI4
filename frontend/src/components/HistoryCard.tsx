// History Card Component - Individual history entry
import React from 'react';
import type { HistoryEntry } from '@/types/history';
import { Clock, Layers, Activity, Zap, Trash2, FolderOpen } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface HistoryCardProps {
  entry: HistoryEntry;
  onLoad: (entry: HistoryEntry) => void;
  onDelete: (id: string) => void;
}

export const HistoryCard: React.FC<HistoryCardProps> = ({ entry, onLoad, onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (showDeleteConfirm) {
      onDelete(entry.id);
      setShowDeleteConfirm(false);
    } else {
      setShowDeleteConfirm(true);
      // Auto-hide confirmation after 3 seconds
      setTimeout(() => setShowDeleteConfirm(false), 3000);
    }
  };

  const handleLoad = (e: React.MouseEvent) => {
    e.stopPropagation();
    onLoad(entry);
  };

  const getPipelineColor = (mode: string): string => {
    switch (mode.toLowerCase()) {
      case 'hybrid':
        return '#61afef';
      case 'sahi':
        return '#98c379';
      case 'high_density':
        return '#e5c07b';
      default:
        return '#c678dd';
    }
  };

  const formatTimestamp = (timestamp: number): string => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return new Date(timestamp).toLocaleString();
    }
  };

  return (
    <div className="bg-industrial-800 rounded-lg border border-industrial-600 hover:border-accent-blue transition-all p-4 group">
      <div className="flex gap-4">
        {/* Thumbnail */}
        <div className="flex-shrink-0">
          <div className="w-32 h-32 rounded-lg overflow-hidden bg-industrial-900 border border-industrial-600">
            <img
              src={entry.thumbnailUrl}
              alt={entry.imageName}
              className="w-full h-full object-cover"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-industrial-100 truncate">
                {entry.imageName}
              </h3>
              <div className="flex items-center gap-2 text-sm text-industrial-400 mt-1">
                <Clock className="w-4 h-4" />
                <span title={new Date(entry.timestamp).toLocaleString()}>
                  {formatTimestamp(entry.timestamp)}
                </span>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="flex items-center gap-2 text-sm">
              <Layers className="w-4 h-4 text-accent-cyan" />
              <span className="text-industrial-300">
                <span className="font-bold text-accent-cyan">
                  {entry.metadata.detectionCount}
                </span>{' '}
                detections
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-accent-green" />
              <span className="text-industrial-300">
                <span className="font-bold text-accent-green">
                  {entry.metadata.instrumentCount}
                </span>{' '}
                instruments
              </span>
            </div>
          </div>

          {/* Pipeline Info */}
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-2 text-sm">
              <Zap className="w-4 h-4" style={{ color: getPipelineColor(entry.metadata.pipelineMode) }} />
              <span
                className="font-medium capitalize"
                style={{ color: getPipelineColor(entry.metadata.pipelineMode) }}
              >
                {entry.metadata.pipelineMode.replace('_', ' ')}
              </span>
            </div>
            <div className="text-sm text-industrial-400">
              {entry.metadata.processingTimeMs.toFixed(0)}ms
            </div>
            <div className="text-xs text-industrial-500 font-mono">
              {entry.metadata.imageSize.width} × {entry.metadata.imageSize.height}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={handleLoad}
              className="flex items-center gap-2 px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-accent-cyan transition-colors text-sm font-medium"
            >
              <FolderOpen className="w-4 h-4" />
              Load
            </button>
            <button
              onClick={handleDelete}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
                showDeleteConfirm
                  ? 'bg-accent-red text-white hover:bg-red-600'
                  : 'bg-industrial-700 text-industrial-300 hover:bg-industrial-600 hover:text-accent-red'
              }`}
            >
              <Trash2 className="w-4 h-4" />
              {showDeleteConfirm ? 'Confirm?' : 'Delete'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
