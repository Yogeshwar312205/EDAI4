// Zustand Store for History Management
import { create } from 'zustand';
import type { HistoryEntry } from '@/types/history';
import type { ProcessingResult, GraphData } from '@/types/api';
import { loadHistoryFromStorage, saveHistoryToStorage, clearHistoryStorage } from '@/utils/historyStorage';
import { generateThumbnail, getImageDimensions } from '@/utils/thumbnailGenerator';
import { saveImageToIDB, getImageFromIDB, deleteImageFromIDB, clearAllImagesFromIDB } from '@/utils/imageDatabase';

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
  
  /**
   * Resolve the full-size image URL for a history entry.
   * Fetches from IndexedDB first (where the full image is stored),
   * then falls back to thumbnailUrl if the full image is unavailable.
   */
  resolveImageUrl: (entry: HistoryEntry) => Promise<string>;

  // Initialization
  initialize: () => void;
}

export const useHistoryStore = create<HistoryState>((set, get) => ({
  entries: [],
  isLoading: false,
  
  /**
   * Initialize store by loading metadata from localStorage.
   * Full images are stored separately in IndexedDB.
   */
  initialize: () => {
    const entries = loadHistoryFromStorage();
    set({ entries });
    console.log(`[History] Loaded ${entries.length} entries from storage`);
  },
  
  /**
   * Add a new history entry.
   * - Metadata (without the full imageUrl) is saved to localStorage.
   * - The full-size imageUrl is saved to IndexedDB.
   */
  addEntry: async (imageName, imageUrl, processingResult, graphData) => {
    try {
      set({ isLoading: true });
      
      console.log('[History] Adding new entry:', imageName);
      
      // Generate thumbnail
      const thumbnailUrl = await generateThumbnail(imageUrl, 150, 150, 0.7);
      
      // Get image dimensions
      const dimensions = await getImageDimensions(imageUrl);
      
      const newId = crypto.randomUUID();

      // Create new entry — imageUrl intentionally omitted from the in-memory
      // entry so the Zustand state stays lean. We always fetch from IDB on load.
      const newEntry: HistoryEntry = {
        id: newId,
        timestamp: Date.now(),
        imageName,
        imageUrl: '', // Not kept in memory or localStorage; stored in IndexedDB
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

      // Persist the full image to IndexedDB (no size limit concerns)
      await saveImageToIDB(newId, imageUrl);
      console.log('[History] Full image saved to IndexedDB:', newId);
      
      // Add to entries (newest first)
      const currentEntries = get().entries;
      const updatedEntries = [newEntry, ...currentEntries];
      
      // Save metadata (no imageUrl) to localStorage
      const saved = saveHistoryToStorage(updatedEntries);
      
      if (saved) {
        set({ entries: updatedEntries, isLoading: false });
        console.log('[History] Entry added successfully:', newEntry.id);
      } else {
        console.error('[History] Failed to save entry metadata to storage');
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('[History] Failed to add entry:', error);
      set({ isLoading: false });
    }
  },
  
  /**
   * Load a history entry (returns the entry for the caller to use).
   * Note: Use resolveImageUrl() separately to get the full-size image.
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
   * Resolve the full-size image URL for a history entry.
   * Tries IndexedDB first, then falls back to thumbnailUrl.
   */
  resolveImageUrl: async (entry: HistoryEntry): Promise<string> => {
    // Try to get the full image from IndexedDB
    const fullImage = await getImageFromIDB(entry.id);
    if (fullImage) {
      console.log('[History] Resolved full image from IndexedDB:', entry.id);
      return fullImage;
    }
    // Fall back to thumbnail (lower quality but better than nothing)
    console.warn('[History] Full image not in IndexedDB, using thumbnail:', entry.id);
    return entry.thumbnailUrl;
  },
  
  /**
   * Delete a history entry and its associated image from IndexedDB.
   */
  deleteEntry: (id: string) => {
    const currentEntries = get().entries;
    const updatedEntries = currentEntries.filter((e) => e.id !== id);
    
    saveHistoryToStorage(updatedEntries);
    set({ entries: updatedEntries });

    // Delete the stored full image from IndexedDB
    deleteImageFromIDB(id).catch((err) =>
      console.error('[History] Failed to delete image from IDB:', id, err)
    );
    
    console.log('[History] Entry deleted:', id);
  },
  
  /**
   * Clear all history and all images from IndexedDB.
   */
  clearAll: () => {
    clearHistoryStorage();
    set({ entries: [] });

    clearAllImagesFromIDB().catch((err) =>
      console.error('[History] Failed to clear images from IDB:', err)
    );
    
    console.log('[History] All entries cleared');
  },
  
  /**
   * Get a specific entry by ID
   */
  getEntry: (id: string) => {
    return get().entries.find((e) => e.id === id);
  },
}));
