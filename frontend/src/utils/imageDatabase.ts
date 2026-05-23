/**
 * IndexedDB wrapper for storing full-size P&ID images.
 *
 * localStorage has only a ~5MB limit, which is too small for base64 image URLs
 * (typically 3–10MB each). IndexedDB supports GB-scale storage and is the
 * correct browser API for large binary/text blobs.
 *
 * Schema:
 *   DB name  : 'edai4_image_store'
 *   Version  : 1
 *   Store    : 'images'
 *   Key      : entry.id  (string UUID)
 *   Value    : base64 data URL string
 */

const DB_NAME = 'edai4_image_store';
const DB_VERSION = 1;
const STORE_NAME = 'images';

/** Open (or create) the IndexedDB database. */
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = (event) => {
      resolve((event.target as IDBOpenDBRequest).result);
    };

    request.onerror = (event) => {
      reject((event.target as IDBOpenDBRequest).error);
    };
  });
}

/**
 * Save a full-size image data URL associated with a history entry ID.
 */
export async function saveImageToIDB(entryId: string, imageUrl: string): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.put(imageUrl, entryId);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
      tx.oncomplete = () => db.close();
    });
  } catch (error) {
    console.error('[ImageDB] Failed to save image:', entryId, error);
    // Non-fatal — history card will fall back to thumbnail
  }
}

/**
 * Retrieve the full-size image data URL for a history entry ID.
 * Returns null if not found or on error.
 */
export async function getImageFromIDB(entryId: string): Promise<string | null> {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(entryId);
      req.onsuccess = () => {
        db.close();
        resolve((req.result as string) ?? null);
      };
      req.onerror = () => {
        db.close();
        resolve(null);
      };
    });
  } catch (error) {
    console.error('[ImageDB] Failed to get image:', entryId, error);
    return null;
  }
}

/**
 * Delete the stored image for a history entry ID.
 */
export async function deleteImageFromIDB(entryId: string): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      store.delete(entryId);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
    });
  } catch (error) {
    console.error('[ImageDB] Failed to delete image:', entryId, error);
  }
}

/**
 * Clear ALL images from IndexedDB (used when clearing all history).
 */
export async function clearAllImagesFromIDB(): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.objectStore(STORE_NAME).clear();
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
    });
  } catch (error) {
    console.error('[ImageDB] Failed to clear images:', error);
  }
}
