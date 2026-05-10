/**
 * Interactive Canvas with DOM-based Bounding Box Overlays
 * BULLETPROOF YOLO BOUNDING BOX ALIGNMENT FIX
 * Uses percentage-based getBoundingClientRect() method for pixel-perfect positioning
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useAppStore } from '@/store/useAppStore';
import type { DetectionResult } from '@/types/api';

interface InteractiveCanvasDOMProps {
  imageUrl: string;
  detections: DetectionResult[];
  imageSize?: { width: number; height: number }; // Optional, uses natural dimensions
}

interface ImageMetrics {
  width: number;
  height: number;
  offsetX: number;
  offsetY: number;
}

export const InteractiveCanvasDOM: React.FC<InteractiveCanvasDOMProps> = ({
  imageUrl,
  detections,
}) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageMetrics, setImageMetrics] = useState<ImageMetrics | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  
  const { selectedNodeId, hoveredNodeId, setHoveredNodeId, setSelectedNodeId } = useAppStore();

  /**
   * BULLETPROOF METHOD: ResizeObserver with getBoundingClientRect()
   * This calculates the EXACT visible footprint of the image, excluding letterbox space
   */
  useEffect(() => {
    if (!imageRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const img = entry.target as HTMLImageElement;
        const rect = img.getBoundingClientRect();
        const naturalW = img.naturalWidth;
        const naturalH = img.naturalHeight;

        if (naturalW === 0 || naturalH === 0) return;

        // Calculate the true active scale factor
        const scale = Math.min(rect.width / naturalW, rect.height / naturalH);

        // Calculate the exact visible rendered width and height in pixels
        const renderedW = naturalW * scale;
        const renderedH = naturalH * scale;

        // Calculate the offsetX and offsetY (the size of the empty letterbox margins)
        const offsetX = (rect.width - renderedW) / 2;
        const offsetY = (rect.height - renderedH) / 2;

        setImageMetrics({ 
          width: renderedW, 
          height: renderedH, 
          offsetX, 
          offsetY 
        });
      }
    });

    observer.observe(imageRef.current);

    // Also trigger on image load
    const handleImageLoad = () => {
      if (!imageRef.current) return;
      const img = imageRef.current;
      const rect = img.getBoundingClientRect();
      const naturalW = img.naturalWidth;
      const naturalH = img.naturalHeight;

      if (naturalW === 0 || naturalH === 0) return;

      const scale = Math.min(rect.width / naturalW, rect.height / naturalH);
      const renderedW = naturalW * scale;
      const renderedH = naturalH * scale;
      const offsetX = (rect.width - renderedW) / 2;
      const offsetY = (rect.height - renderedH) / 2;

      setImageMetrics({ 
        width: renderedW, 
        height: renderedH, 
        offsetX, 
        offsetY 
      });
    };

    imageRef.current.addEventListener('load', handleImageLoad);
    
    // Trigger initial calculation if image already loaded
    if (imageRef.current.complete) {
      handleImageLoad();
    }

    return () => {
      observer.disconnect();
      if (imageRef.current) {
        imageRef.current.removeEventListener('load', handleImageLoad);
      }
    };
  }, []);

  /**
   * Convert YOLO bbox to CSS percentages
   * Backend sends [x1, y1, x2, y2] as top-left and bottom-right corners (already in correct format)
   */
  const bboxToPercentages = useCallback(
    (bbox: { x1: number; y1: number; x2: number; y2: number }) => {
      if (!imageRef.current) return null;

      const naturalWidth = imageRef.current.naturalWidth;
      const naturalHeight = imageRef.current.naturalHeight;

      if (naturalWidth === 0 || naturalHeight === 0) return null;

      // Backend already sends top-left (x1, y1) and bottom-right (x2, y2)
      // No center-to-top-left conversion needed!
      const x1 = bbox.x1;
      const y1 = bbox.y1;
      const x2 = bbox.x2;
      const y2 = bbox.y2;

      // Convert to CSS percentages based on natural image dimensions
      const leftPct = (x1 / naturalWidth) * 100;
      const topPct = (y1 / naturalHeight) * 100;
      const widthPct = ((x2 - x1) / naturalWidth) * 100;
      const heightPct = ((y2 - y1) / naturalHeight) * 100;

      return {
        left: `${leftPct}%`,
        top: `${topPct}%`,
        width: `${widthPct}%`,
        height: `${heightPct}%`,
      };
    },
    []
  );

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
   * Zoom to specific detection
   */
  useEffect(() => {
    if (selectedNodeId && imageMetrics) {
      const index = parseInt(selectedNodeId.replace('node_', ''));
      
      if (index >= 0 && index < detections.length) {
        const detection = detections[index];
        const coords = bboxToPercentages(detection.bbox);
        
        if (coords && containerRef.current) {
          // Parse percentage values to get center
          const leftPct = parseFloat(coords.left);
          const topPct = parseFloat(coords.top);
          const widthPct = parseFloat(coords.width);
          const heightPct = parseFloat(coords.height);
          
          // Calculate center in pixels
          const centerX = imageMetrics.offsetX + (leftPct + widthPct / 2) * imageMetrics.width / 100;
          const centerY = imageMetrics.offsetY + (topPct + heightPct / 2) * imageMetrics.height / 100;
          
          // Zoom to 2x
          const newZoom = 2;
          setZoom(newZoom);
          
          // Pan to center the detection
          const containerRect = containerRef.current.getBoundingClientRect();
          setPan({
            x: containerRect.width / 2 - centerX * newZoom,
            y: containerRect.height / 2 - centerY * newZoom,
          });
        }
      }
    }
  }, [selectedNodeId, detections, imageMetrics, bboxToPercentages]);

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
        {/* P&ID Image */}
        <img
          ref={imageRef}
          src={imageUrl}
          alt="P&ID Diagram"
          className="max-w-full max-h-full object-contain"
          draggable={false}
          style={{ userSelect: 'none' }}
        />

        {/* Inner Wrapper - Perfectly covers only the visible image */}
        {imageMetrics && (
          <div
            className="absolute pointer-events-none"
            style={{
              width: `${imageMetrics.width}px`,
              height: `${imageMetrics.height}px`,
              left: `${imageMetrics.offsetX}px`,
              top: `${imageMetrics.offsetY}px`,
            }}
          >
            {/* Bounding Box Overlays - Using CSS Percentages */}
            {detections.map((detection, index) => {
              const nodeId = `node_${index}`;
              const isSelected = selectedNodeId === nodeId;
              const isHovered = hoveredNodeId === nodeId;
              const coords = bboxToPercentages(detection.bbox);
              
              if (!coords) return null;

              const color = getClassColor(detection.class_name);

              return (
                <div
                  key={nodeId}
                  className="absolute pointer-events-auto"
                  style={{
                    left: coords.left,
                    top: coords.top,
                    width: coords.width,
                    height: coords.height,
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
        )}
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

      {/* Debug Info - Shows exact metrics */}
      {imageMetrics && (
        <div className="absolute top-4 left-4 bg-industrial-800/90 backdrop-blur-sm rounded-lg p-2 border border-industrial-600 text-xs font-mono text-industrial-400">
          <div className="font-bold text-accent-blue mb-1">🎯 Bulletproof Metrics</div>
          <div>Natural: {imageRef.current?.naturalWidth} × {imageRef.current?.naturalHeight}</div>
          <div>Rendered: {imageMetrics.width.toFixed(1)} × {imageMetrics.height.toFixed(1)}</div>
          <div>Offset: {imageMetrics.offsetX.toFixed(1)}, {imageMetrics.offsetY.toFixed(1)}</div>
          <div>Scale: {(imageMetrics.width / (imageRef.current?.naturalWidth || 1)).toFixed(4)}</div>
          <div className="pt-1 border-t border-industrial-600 mt-1">
            Detections: {detections.length}
          </div>
          {detections.length > 0 && (
            <div className="pt-1 border-t border-industrial-600 mt-1 text-green-400">
              ✅ Using top-left coords (no center shift)
            </div>
          )}
        </div>
      )}
    </div>
  );
};
