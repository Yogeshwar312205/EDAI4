// LocalStorage utilities for History
import type { HistoryEntry, HistoryStorage } from '@/types/history';

const STORAGE_KEY = 'edai4_history';
const MAX_ENTRIES = 50;
const STORAGE_VERSION = '1.0';

/**
 * Load history from localStorage
 */
export function loadHistoryFromStorage(): HistoryEntry[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];

    const data: HistoryStorage = JSON.parse(stored);
    
    // Version check for future migrations
    if (data.version !== STORAGE_VERSION) {
      console.warn('History version mismatch, migrating...');
      // Future: Add migration logic here
    }

    return data.entries || [];
  } catch (error) {
    console.error('Failed to load history from storage:', error);
    return [];
  }
}

/**
 * Save history to localStorage
 */
export function saveHistoryToStorage(entries: HistoryEntry[]): boolean {
  try {
    // Limit entries to MAX_ENTRIES (keep most recent)
    const limitedEntries = entries
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, MAX_ENTRIES);

    const data: HistoryStorage = {
      entries: limitedEntries,
      maxEntries: MAX_ENTRIES,
      version: STORAGE_VERSION,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    return true;
  } catch (error) {
    console.error('Failed to save history to storage:', error);
    
    // Check if quota exceeded
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      console.warn('LocalStorage quota exceeded. Removing oldest entries...');
      
      // Try again with fewer entries
      const reducedEntries = entries.slice(0, Math.floor(MAX_ENTRIES / 2));
      try {
        const data: HistoryStorage = {
          entries: reducedEntries,
          maxEntries: MAX_ENTRIES,
          version: STORAGE_VERSION,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        return true;
      } catch (retryError) {
        console.error('Failed to save even with reduced entries:', retryError);
        return false;
      }
    }
    
    return false;
  }
}

/**
 * Clear all history from localStorage
 */
export function clearHistoryStorage(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear history storage:', error);
  }
}

/**
 * Get storage usage estimate
 */
export function getStorageUsage(): { used: number; total: number; percentage: number } {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const usedBytes = stored ? new Blob([stored]).size : 0;
    const totalBytes = 5 * 1024 * 1024; // Assume 5MB limit
    
    return {
      used: usedBytes,
      total: totalBytes,
      percentage: (usedBytes / totalBytes) * 100,
    };
  } catch (error) {
    console.error('Failed to get storage usage:', error);
    return { used: 0, total: 0, percentage: 0 };
  }
}
