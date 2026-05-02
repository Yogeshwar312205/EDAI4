// Debug Overlay for Canvas Alignment Verification
import React from 'react';

interface CanvasDebugOverlayProps {
  imageSize: { width: number; height: number };
  canvasSize: { width: number; height: number };
  scale: {
    uniformScale: number;
    marginX: number;
    marginY: number;
    displayWidth: number;
    displayHeight: number;
  };
  transform: {
    scale: number;
    offsetX: number;
    offsetY: number;
  };
  detectionCount: number;
}

export const CanvasDebugOverlay: React.FC<CanvasDebugOverlayProps> = ({
  imageSize,
  canvasSize,
  scale,
  transform,
  detectionCount,
}) => {
  return (
    <div className="absolute top-4 left-4 bg-industrial-800/95 backdrop-blur-sm rounded-lg p-4 border border-industrial-600 font-mono text-xs max-w-sm">
      <h3 className="text-accent-blue font-bold mb-3 text-sm">🔍 Canvas Debug Info</h3>
      
      {/* Image Dimensions */}
      <div className="mb-3">
        <div className="text-industrial-400 mb-1">Image (Natural)</div>
        <div className="text-industrial-200">
          {imageSize.width} × {imageSize.height} px
        </div>
      </div>
      
      {/* Canvas Dimensions */}
      <div className="mb-3">
        <div className="text-industrial-400 mb-1">Canvas (Display)</div>
        <div className="text-industrial-200">
          {canvasSize.width} × {canvasSize.height} px
        </div>
      </div>
      
      {/* Scaling Info */}
      <div className="mb-3">
        <div className="text-industrial-400 mb-1">Scaling</div>
        <div className="text-industrial-200 space-y-1">
          <div>Uniform: {scale.uniformScale.toFixed(4)}</div>
          <div>Display: {scale.displayWidth.toFixed(0)} × {scale.displayHeight.toFixed(0)}</div>
          <div>Margins: ({scale.marginX.toFixed(0)}, {scale.marginY.toFixed(0)})</div>
        </div>
      </div>
      
      {/* Transform Info */}
      <div className="mb-3">
        <div className="text-industrial-400 mb-1">Transform</div>
        <div className="text-industrial-200 space-y-1">
          <div>Zoom: {(transform.scale * 100).toFixed(0)}%</div>
          <div>Pan: ({transform.offsetX.toFixed(0)}, {transform.offsetY.toFixed(0)})</div>
        </div>
      </div>
      
      {/* Detection Count */}
      <div className="mb-3">
        <div className="text-industrial-400 mb-1">Detections</div>
        <div className="text-accent-green font-bold">
          {detectionCount} boxes
        </div>
      </div>
      
      {/* Alignment Check */}
      <div className="pt-3 border-t border-industrial-600">
        <div className="text-industrial-400 mb-2">Alignment Check</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${scale.uniformScale > 0 ? 'bg-accent-green' : 'bg-accent-red'}`} />
            <span className="text-industrial-300">Uniform Scale</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${scale.marginX >= 0 && scale.marginY >= 0 ? 'bg-accent-green' : 'bg-accent-red'}`} />
            <span className="text-industrial-300">Margins Calculated</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${detectionCount > 0 ? 'bg-accent-green' : 'bg-accent-yellow'}`} />
            <span className="text-industrial-300">Detections Loaded</span>
          </div>
        </div>
      </div>
      
      {/* Formula Display */}
      <div className="pt-3 border-t border-industrial-600 mt-3">
        <div className="text-industrial-400 mb-2">Coordinate Formula</div>
        <div className="bg-industrial-900 p-2 rounded text-[10px] text-industrial-300 leading-relaxed">
          <div>canvasX = (imgX × {scale.uniformScale.toFixed(3)})</div>
          <div className="ml-8">+ {scale.marginX.toFixed(1)}</div>
          <div className="ml-8">× {transform.scale.toFixed(2)}</div>
          <div className="ml-8">+ {transform.offsetX.toFixed(0)}</div>
        </div>
      </div>
      
      {/* Tips */}
      <div className="pt-3 border-t border-industrial-600 mt-3">
        <div className="text-industrial-400 mb-2">💡 Tips</div>
        <ul className="text-industrial-300 space-y-1 text-[10px]">
          <li>• Uniform scale should be &lt; 1.0</li>
          <li>• Margins should be positive</li>
          <li>• Display size ≤ canvas size</li>
          <li>• Zoom 100% = scale 1.0</li>
        </ul>
      </div>
    </div>
  );
};

// Hook to enable/disable debug overlay
export const useCanvasDebug = () => {
  const [debugEnabled, setDebugEnabled] = React.useState(false);
  
  React.useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Press 'D' key to toggle debug overlay
      if (e.key === 'd' || e.key === 'D') {
        setDebugEnabled(prev => !prev);
      }
    };
    
    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, []);
  
  return { debugEnabled, setDebugEnabled };
};
