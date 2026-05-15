// Zustand Store for History Management
import { create } from 'zustand';
import type { HistoryEntry } from '@/types/history';
import type { ProcessingResult, GraphData } from '@/types/api';
import { loadHistoryFromStorage, saveHistoryToStorage, clearHistoryStorage } from '@/utils/historyStorage';
import { generateThumbnail, getImageDimensions } from '@/utils/thumbnailGenerator';

interface HistoryState {
  entries: HistoryEntry[];
  isLoading: boolean;
  
  // Actions
  addEntry: (
    imageName: string,
    imageUrl: string,
    processingResult: ProcessingResult,
    graphData: GraphData | null
  ) => Promise<void>;
  loadEntry: (id: string) => HistoryEntry | null;
  deleteEntry: (id: string) => void;
  clearAll: () => void;
  getEntry: (id: string) => HistoryEntry | undefined;
  
  // Initialization
  initialize: () => void;
}

export const useHistoryStore = create<HistoryState>((set, get) => ({
  entries: [],
  isLoading: false,
  
  /**
   * Initialize store by loading from localStorage
   */
  initialize: () => {
    const entries = loadHistoryFromStorage();
    set({ entries });
    console.log(`[History] Loaded ${entries.length} entries from storage`);
  },
  
  /**
   * Add a new history entry
   */
  addEntry: async (imageName, imageUrl, processingResult, graphData) => {
    try {
      set({ isLoading: true });
      
      console.log('[History] Adding new entry:', imageName);
      
      // Generate thumbnail
      const thumbnailUrl = await generateThumbnail(imageUrl, 150, 150, 0.7);
      
      // Get image dimensions
      const dimensions = await getImageDimensions(imageUrl);
      
      // Create new entry
      const newEntry: HistoryEntry = {
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        imageName,
        imageUrl,
        thumbnailUrl,
        processingResult,
        graphData,
        metadata: {
          processingTimeMs: processingResult.processing_time_ms,
          detectionCount: processingResult.layer1_detections,
          instrumentCount: processingResult.layer2_instruments,
          pipelineMode: processingResult.graph_summary?.mode || 'unknown',
          imageSize: dimensions,
        },
      };
      
      // Add to entries (newest first)
      const currentEntries = get().entries;
      const updatedEntries = [newEntry, ...currentEntries];
      
      // Save to storage
      const saved = saveHistoryToStorage(updatedEntries);
      
      if (saved) {
        set({ entries: updatedEntries, isLoading: false });
        console.log('[History] Entry added successfully:', newEntry.id);
      } else {
        console.error('[History] Failed to save entry to storage');
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('[History] Failed to add entry:', error);
      set({ isLoading: false });
    }
  },
  
  /**
   * Load a history entry (returns the entry for the caller to use)
   */
  loadEntry: (id: string) => {
    const entry = get().entries.find((e) => e.id === id);
    if (entry) {
      console.log('[History] Loading entry:', entry.imageName);
      return entry;
    }
    console.warn('[History] Entry not found:', id);
    return null;
  },
  
  /**
   * Delete a history entry
   */
  deleteEntry: (id: string) => {
    const currentEntries = get().entries;
    const updatedEntries = currentEntries.filter((e) => e.id !== id);
    
    saveHistoryToStorage(updatedEntries);
    set({ entries: updatedEntries });
    
    console.log('[History] Entry deleted:', id);
  },
  
  /**
   * Clear all history
   */
  clearAll: () => {
    clearHistoryStorage();
    set({ entries: [] });
    console.log('[History] All entries cleared');
  },
  
  /**
   * Get a specific entry by ID
   */
  getEntry: (id: string) => {
    return get().entries.find((e) => e.id === id);
  },
}));
