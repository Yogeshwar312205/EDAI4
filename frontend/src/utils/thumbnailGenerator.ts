// Thumbnail generation utility

/**
 * Generate a thumbnail from an image URL
 * @param imageUrl - Original image URL (data URL or blob URL)
 * @param maxWidth - Maximum thumbnail width (default: 150)
 * @param maxHeight - Maximum thumbnail height (default: 150)
 * @param quality - JPEG quality 0-1 (default: 0.7)
 * @returns Promise<string> - Thumbnail data URL
 */
export async function generateThumbnail(
  imageUrl: string,
  maxWidth: number = 150,
  maxHeight: number = 150,
  quality: number = 0.7
): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => {
      try {
        // Calculate scaled dimensions (maintain aspect ratio)
        let width = img.width;
        let height = img.height;
        
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
          }
        }
        
        // Create canvas and draw scaled image
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Failed to get canvas context'));
          return;
        }
        
        // Use better image smoothing
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        
        // Draw image
        ctx.drawImage(img, 0, 0, width, height);
        
        // Convert to data URL (JPEG for better compression)
        const thumbnailUrl = canvas.toDataURL('image/jpeg', quality);
        resolve(thumbnailUrl);
      } catch (error) {
        reject(error);
      }
    };
    
    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };
    
    img.src = imageUrl;
  });
}

/**
 * Get image dimensions from URL
 */
export async function getImageDimensions(imageUrl: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => {
      resolve({
        width: img.naturalWidth,
        height: img.naturalHeight,
      });
    };
    
    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };
    
    img.src = imageUrl;
  });
}
