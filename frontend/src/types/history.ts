// History Type Definitions
import type { ProcessingResult, GraphData } from './api';

export interface HistoryEntry {
  id: string;                          // Unique ID (UUID)
  timestamp: number;                   // Unix timestamp
  imageName: string;                   // Original filename
  imageUrl: string;                    // Base64 data URL
  thumbnailUrl: string;                // Smaller thumbnail for list view
  processingResult: ProcessingResult;  // Full processing result
  graphData: GraphData | null;         // Graph topology
  metadata: {
    processingTimeMs: number;
    detectionCount: number;
    instrumentCount: number;
    pipelineMode: string;              // "hybrid", "sahi", etc.
    imageSize: {
      width: number;
      height: number;
    };
  };
  tags?: string[];                     // User-added tags (future)
  notes?: string;                      // User notes (future)
}

export interface HistoryStorage {
  entries: HistoryEntry[];
  maxEntries: number;
  version: string;
}
