/**
 * Interactive Canvas with DOM-based Bounding Box Overlays
 * SIMPLIFIED COORDINATE FIX - Backend sends percentages, React multiplies by 100!
 * No complex math, no resize bugs, resolution-independent!
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useAppStore } from '@/store/useAppStore';
import type { DetectionResult } from '@/types/api';

interface InteractiveCanvasDOMProps {
  imageUrl: string;
  detections: DetectionResult[];
  imageSize?: { width: number; height: number }; // Optional, not needed anymore!
}

export const InteractiveCanvasDOM: React.FC<InteractiveCanvasDOMProps> = ({
  imageUrl,
  detections,
}) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  
  const { selectedNodeId, hoveredNodeId, setHoveredNodeId, setSelectedNodeId } = useAppStore();

  // Debug logging
  console.log('[InteractiveCanvasDOM] Rendering with:', {
    imageUrl: imageUrl ? 'present' : 'missing',
    detectionsCount: detections?.length || 0,
    imageLoaded,
  });

  // Validate detections
  React.useEffect(() => {
    if (detections && detections.length > 0) {
      console.log('[InteractiveCanvasDOM] First detection:', detections[0]);
      
      // Check if detections have the correct format
      const firstDet = detections[0];
      if (!firstDet.pct_x && !firstDet.pct_y) {
        console.error('[InteractiveCanvasDOM] ERROR: Detections missing percentage coordinates!', firstDet);
      }
    }
  }, [detections]);

  /**
   * SIMPLIFIED: Just wait for image to load
   * No complex ResizeObserver or getBoundingClientRect needed!
   */
  useEffect(() => {
    if (!imageRef.current) return;

    const handleImageLoad = () => {
      setImageLoaded(true);
      console.log('✅ Image loaded - using percentage coordinates!');
    };

    imageRef.current.addEventListener('load', handleImageLoad);
    
    // Trigger if already loaded
    if (imageRef.current.complete) {
      handleImageLoad();
    }

    return () => {
      if (imageRef.current) {
        imageRef.current.removeEventListener('load', handleImageLoad);
      }
    };
  }, [imageUrl]);

  /**
   * SIMPLIFIED: Convert backend percentages to CSS percentages
   * Backend sends 0.0 to 1.0, we just multiply by 100!
   */
  const getBoxStyle = useCallback((detection: DetectionResult) => {
    return {
      left: `${detection.pct_x * 100}%`,
      top: `${detection.pct_y * 100}%`,
      width: `${detection.pct_width * 100}%`,
      height: `${detection.pct_height * 100}%`,
    };
  }, []);

  /**
   * Handle mouse wheel zoom
   */
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.5, Math.min(5, zoom * delta));
    setZoom(newZoom);
  }, [zoom]);

  /**
   * Handle pan start
   */
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) { // Left click only
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  }, [pan]);

  /**
   * Handle pan move
   */
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      });
    }
  }, [isPanning, panStart]);

  /**
   * Handle pan end
   */
  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  /**
   * Reset zoom and pan
   */
  const handleReset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  /**
   * Zoom to specific detection (simplified)
   */
  useEffect(() => {
    if (selectedNodeId && imageLoaded && imageRef.current) {
      const index = parseInt(selectedNodeId.replace('node_', ''));
      
      if (index >= 0 && index < detections.length) {
        const detection = detections[index];
        
        // Calculate center from percentage coordinates
        const centerXPct = detection.pct_x + detection.pct_width / 2;
        const centerYPct = detection.pct_y + detection.pct_height / 2;
        
        // Convert to pixels
        const naturalW = imageRef.current.naturalWidth;
        const naturalH = imageRef.current.naturalHeight;
        const centerX = centerXPct * naturalW;
        const centerY = centerYPct * naturalH;
        
        // Zoom to 2x
        const newZoom = 2;
        setZoom(newZoom);
        
        // Pan to center the detection
        if (containerRef.current) {
          const containerRect = containerRef.current.getBoundingClientRect();
          setPan({
            x: containerRect.width / 2 - centerX * newZoom,
            y: containerRect.height / 2 - centerY * newZoom,
          });
        }
      }
    }
  }, [selectedNodeId, detections, imageLoaded]);

  /**
   * Get color based on class
   */
  const getClassColor = (className: string): string => {
    if (className.includes('instrument')) return '#61afef';
    if (className.includes('valve')) return '#56b6c2';
    if (className.includes('equipment')) return '#98c379';
    if (className.includes('pump')) return '#e5c07b';
    return '#c678dd';
  };

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-industrial-900 rounded-lg overflow-hidden relative cursor-grab active:cursor-grabbing"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Image Container with Transform */}
      <div
        className="absolute inset-0 flex items-center justify-center"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
          transition: isPanning ? 'none' : 'transform 0.3s ease-out',
        }}
      >
        {/* P&ID Image with Bounding Boxes */}
        <div className="relative">
          <img
            ref={imageRef}
            src={imageUrl}
            alt="P&ID Diagram"
            className="max-w-full max-h-full object-contain"
            draggable={false}
            style={{ userSelect: 'none' }}
          />

          {/* SIMPLIFIED: Bounding Box Overlays - Direct Percentage Positioning */}
          {imageLoaded && detections.map((detection, index) => {
            const nodeId = `node_${index}`;
            const isSelected = selectedNodeId === nodeId;
            const isHovered = hoveredNodeId === nodeId;
            const boxStyle = getBoxStyle(detection);  // Just multiply by 100!
            const color = getClassColor(detection.class_name);

            return (
              <div
                key={nodeId}
                className="absolute pointer-events-auto"
                style={{
                  ...boxStyle,  // Just use the percentages directly!
                  border: `${isSelected ? 4 : isHovered ? 3 : 2}px solid ${color}`,
                  boxShadow: isSelected || isHovered ? `0 0 20px ${color}` : 'none',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={() => setHoveredNodeId(nodeId)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId(nodeId);
                }}
              >
                {/* Tag Label */}
                {detection.tag && (
                  <div
                    className="absolute -top-6 left-0 px-2 py-1 rounded text-xs font-bold font-mono whitespace-nowrap"
                    style={{
                      backgroundColor: color,
                      color: '#0a0e14',
                    }}
                  >
                    {detection.tag}
                  </div>
                )}

                {/* Hover Tooltip */}
                {isHovered && (
                  <div
                    className="absolute left-full ml-2 top-0 w-48 bg-industrial-800 border-2 rounded-lg p-3 shadow-2xl z-50"
                    style={{
                      borderColor: color,
                    }}
                  >
                    <div className="text-xs space-y-1 font-mono">
                      <div className="text-industrial-300">
                        Tag: <span className="text-industrial-100">{detection.tag || 'N/A'}</span>
                      </div>
                      <div className="text-industrial-400">
                        Class: {detection.class_name}
                      </div>
                      <div style={{ color }}>
                        Confidence: {(detection.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Controls Overlay */}
      <div className="absolute bottom-4 right-4 bg-industrial-800/90 backdrop-blur-sm rounded-lg p-3 border border-industrial-600 pointer-events-auto">
        <div className="text-xs text-industrial-300 space-y-1 font-mono">
          <div>🖱️ Drag to pan</div>
          <div>🔍 Scroll to zoom</div>
          <div>📍 Click box to select</div>
          <div className="pt-2 border-t border-industrial-600">
            Zoom: {(zoom * 100).toFixed(0)}%
          </div>
          <button
            onClick={handleReset}
            className="mt-2 w-full px-2 py-1 bg-accent-blue text-white rounded text-xs hover:bg-accent-cyan transition-colors"
          >
            Reset View
          </button>
        </div>
      </div>

      {/* Debug Info - Shows percentage-based coordinates */}
      {imageLoaded && (
        <div className="absolute top-4 left-4 bg-industrial-800/90 backdrop-blur-sm rounded-lg p-2 border border-industrial-600 text-xs font-mono text-industrial-400">
          <div className="font-bold text-green-400 mb-1">✅ Percentage-Based Coordinates</div>
          <div>Natural: {imageRef.current?.naturalWidth} × {imageRef.current?.naturalHeight}</div>
          <div>Detections: {detections.length}</div>
          <div className="pt-1 border-t border-industrial-600 mt-1 text-green-400">
            Backend sends percentages (0.0-1.0)
          </div>
          <div className="text-green-400">
            React multiplies by 100 for CSS
          </div>
          <div className="text-green-400">
            No scaling math needed! 🎉
          </div>
        </div>
      )}
    </div>
  );
};
