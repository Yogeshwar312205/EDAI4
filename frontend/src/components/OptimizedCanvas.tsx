// Optimized Interactive Canvas with Perfect Bounding Box Alignment and 60 FPS Performance
import React, { useRef, useEffect, useCallback, useMemo } from 'react';
import { useAppStore } from '@/store/useAppStore';
import type { DetectionResult } from '@/types/api';

interface OptimizedCanvasProps {
  imageUrl: string;
  detections: DetectionResult[];
  imageSize: { width: number; height: number };
}

interface Transform {
  scale: number;
  offsetX: number;
  offsetY: number;
}

export const OptimizedCanvas: React.FC<OptimizedCanvasProps> = ({
  imageUrl,
  detections,
  imageSize,
}) => {
  // Canvas refs
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Image ref
  const imageRef = useRef<HTMLImageElement | null>(null);
  
  // Transform state using refs (no re-renders on pan/zoom)
  const transformRef = useRef<Transform>({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
  });
  
  // Pan state
  const isPanningRef = useRef(false);
  const lastPanPointRef = useRef({ x: 0, y: 0 });
  
  // Animation frame ref
  const rafIdRef = useRef<number | null>(null);
  const needsRedrawRef = useRef(true);
  
  // Image scaling factors (for bounding box alignment)
  const imageScaleRef = useRef({
    scaleX: 1,
    scaleY: 1,
    uniformScale: 1,
    marginX: 0,
    marginY: 0,
    displayWidth: 0,
    displayHeight: 0,
  });
  
  const { selectedNodeId, hoveredNodeId, setHoveredNodeId, setSelectedNodeId } = useAppStore();
  const hoveredNodeIdRef = useRef(hoveredNodeId);
  const selectedNodeIdRef = useRef(selectedNodeId);
  
  // Memoize valid detections (filter out invalid ones)
  const validDetections = useMemo(() => {
    return detections.filter(detection => {
      const bbox = detection.bbox;
      // Filter out invalid bounding boxes
      if (!bbox || bbox.x1 >= bbox.x2 || bbox.y1 >= bbox.y2) {
        return false;
      }
      // Filter out boxes outside image bounds
      if (bbox.x1 < 0 || bbox.y1 < 0 || bbox.x2 > imageSize.width || bbox.y2 > imageSize.height) {
        return false;
      }
      // Filter out very small boxes (likely noise)
      const width = bbox.x2 - bbox.x1;
      const height = bbox.y2 - bbox.y1;
      if (width < 5 || height < 5) {
        return false;
      }
      return true;
    });
  }, [detections, imageSize]);
  
  // Update refs when props change
  useEffect(() => {
    hoveredNodeIdRef.current = hoveredNodeId;
    needsRedrawRef.current = true;
  }, [hoveredNodeId]);
  
  useEffect(() => {
    selectedNodeIdRef.current = selectedNodeId;
    needsRedrawRef.current = true;
  }, [selectedNodeId]);

  // Calculate image scaling with object-fit: contain logic
  const calculateImageScale = useCallback((
    canvasWidth: number,
    canvasHeight: number,
    imgWidth: number,
    imgHeight: number
  ) => {
    // Calculate scale to fit image in canvas (object-fit: contain)
    const scaleX = canvasWidth / imgWidth;
    const scaleY = canvasHeight / imgHeight;
    const uniformScale = Math.min(scaleX, scaleY);
    
    // Calculate display dimensions
    const displayWidth = imgWidth * uniformScale;
    const displayHeight = imgHeight * uniformScale;
    
    // Calculate margins (centering)
    const marginX = (canvasWidth - displayWidth) / 2;
    const marginY = (canvasHeight - displayHeight) / 2;
    
    return {
      scaleX,
      scaleY,
      uniformScale,
      marginX,
      marginY,
      displayWidth,
      displayHeight,
    };
  }, []);

  // Convert image coordinates to canvas coordinates
  const imageToCanvas = useCallback((x: number, y: number) => {
    const scale = imageScaleRef.current;
    const transform = transformRef.current;
    
    // Apply uniform scaling and margins
    const canvasX = (x * scale.uniformScale + scale.marginX) * transform.scale + transform.offsetX;
    const canvasY = (y * scale.uniformScale + scale.marginY) * transform.scale + transform.offsetY;
    
    return { x: canvasX, y: canvasY };
  }, []);

  // Convert canvas coordinates to image coordinates
  const canvasToImage = useCallback((canvasX: number, canvasY: number) => {
    const scale = imageScaleRef.current;
    const transform = transformRef.current;
    
    // Reverse the transformation
    const x = ((canvasX - transform.offsetX) / transform.scale - scale.marginX) / scale.uniformScale;
    const y = ((canvasY - transform.offsetY) / transform.scale - scale.marginY) / scale.uniformScale;
    
    return { x, y };
  }, []);

  // Get color based on class
  const getClassColor = useCallback((className: string): string => {
    if (className.includes('instrument')) return '#61afef';
    if (className.includes('valve')) return '#56b6c2';
    if (className.includes('equipment')) return '#98c379';
    if (className.includes('pump')) return '#e5c07b';
    return '#c678dd';
  }, []);

  // Main render function (called by requestAnimationFrame) - optimized
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d', { alpha: false });
    const img = imageRef.current;
    
    if (!canvas || !ctx || !img) return;
    
    const scale = imageScaleRef.current;
    const transform = transformRef.current;
    
    // Clear canvas
    ctx.fillStyle = '#0a0e14'; // industrial-900
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Save context state
    ctx.save();
    
    // Apply pan and zoom transformations
    ctx.translate(transform.offsetX, transform.offsetY);
    ctx.scale(transform.scale, transform.scale);
    
    // Draw image with proper scaling and centering
    ctx.drawImage(
      img,
      scale.marginX,
      scale.marginY,
      scale.displayWidth,
      scale.displayHeight
    );
    
    // Use validDetections instead of detections
    validDetections.forEach((detection, index) => {
      const nodeId = `node_${index}`;
      const isSelected = selectedNodeIdRef.current === nodeId;
      const isHovered = hoveredNodeIdRef.current === nodeId;
      const bbox = detection.bbox;
      const color = getClassColor(detection.class_name);
      
      // Convert image coordinates to canvas coordinates (before transform)
      const x1 = bbox.x1 * scale.uniformScale + scale.marginX;
      const y1 = bbox.y1 * scale.uniformScale + scale.marginY;
      const x2 = bbox.x2 * scale.uniformScale + scale.marginX;
      const y2 = bbox.y2 * scale.uniformScale + scale.marginY;
      const width = x2 - x1;
      const height = y2 - y1;
      
      // Skip if box is too small to render
      if (width < 1 || height < 1) return;
      
      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = (isSelected ? 4 : isHovered ? 3 : 2) / transform.scale;
      
      if (isSelected || isHovered) {
        ctx.shadowBlur = 10 / transform.scale;
        ctx.shadowColor = color;
      } else {
        ctx.shadowBlur = 0;
      }
      
      ctx.strokeRect(x1, y1, width, height);
      ctx.shadowBlur = 0;
      
      // Draw tag label
      if (detection.tag) {
        const fontSize = 14 / transform.scale;
        const padding = 5 / transform.scale;
        const labelHeight = 20 / transform.scale;
        
        ctx.font = `bold ${fontSize}px monospace`;
        const textWidth = ctx.measureText(detection.tag).width;
        
        // Label background
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.9;
        ctx.fillRect(x1, y1 - labelHeight, textWidth + padding * 2, labelHeight);
        ctx.globalAlpha = 1;
        
        // Label text
        ctx.fillStyle = '#0a0e14';
        ctx.textBaseline = 'top';
        ctx.fillText(detection.tag, x1 + padding, y1 - labelHeight + padding / 2);
      }
      
      // Draw hover tooltip (only if hovered, not selected)
      if (isHovered && !isSelected) {
        const tooltipX = x2 + 10 / transform.scale;
        const tooltipY = y1;
        const tooltipWidth = 200 / transform.scale;
        const tooltipHeight = 80 / transform.scale;
        const fontSize = 12 / transform.scale;
        const padding = 10 / transform.scale;
        
        // Tooltip background
        ctx.fillStyle = '#1a1f29';
        ctx.strokeStyle = color;
        ctx.lineWidth = 2 / transform.scale;
        ctx.shadowBlur = 15 / transform.scale;
        ctx.shadowColor = color;
        ctx.globalAlpha = 0.95;
        
        // Rounded rectangle
        const radius = 8 / transform.scale;
        ctx.beginPath();
        ctx.moveTo(tooltipX + radius, tooltipY);
        ctx.lineTo(tooltipX + tooltipWidth - radius, tooltipY);
        ctx.quadraticCurveTo(tooltipX + tooltipWidth, tooltipY, tooltipX + tooltipWidth, tooltipY + radius);
        ctx.lineTo(tooltipX + tooltipWidth, tooltipY + tooltipHeight - radius);
        ctx.quadraticCurveTo(tooltipX + tooltipWidth, tooltipY + tooltipHeight, tooltipX + tooltipWidth - radius, tooltipY + tooltipHeight);
        ctx.lineTo(tooltipX + radius, tooltipY + tooltipHeight);
        ctx.quadraticCurveTo(tooltipX, tooltipY + tooltipHeight, tooltipX, tooltipY + tooltipHeight - radius);
        ctx.lineTo(tooltipX, tooltipY + radius);
        ctx.quadraticCurveTo(tooltipX, tooltipY, tooltipX + radius, tooltipY);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
        
        // Tooltip text
        ctx.font = `${fontSize}px monospace`;
        ctx.textBaseline = 'top';
        
        ctx.fillStyle = '#abb2bf';
        ctx.fillText(`Tag: ${detection.tag || 'N/A'}`, tooltipX + padding, tooltipY + padding);
        
        ctx.fillStyle = '#828997';
        ctx.fillText(`Class: ${detection.class_name}`, tooltipX + padding, tooltipY + padding + fontSize * 1.5);
        
        ctx.fillStyle = color;
        ctx.fillText(`Confidence: ${(detection.confidence * 100).toFixed(1)}%`, tooltipX + padding, tooltipY + padding + fontSize * 3);
      }
    });
    
    // Restore context state
    ctx.restore();
    
    needsRedrawRef.current = false;
  }, [validDetections, getClassColor]);

  // Animation loop using requestAnimationFrame
  const animate = useCallback(() => {
    if (needsRedrawRef.current) {
      render();
    }
    rafIdRef.current = requestAnimationFrame(animate);
  }, [render]);

  // Load image
  useEffect(() => {
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.src = imageUrl;
    
    img.onload = () => {
      imageRef.current = img;
      
      const canvas = canvasRef.current;
      const container = containerRef.current;
      
      if (canvas && container) {
        // Calculate image scale
        imageScaleRef.current = calculateImageScale(
          canvas.width,
          canvas.height,
          imageSize.width,
          imageSize.height
        );
        
        // Initial fit
        transformRef.current = {
          scale: 1,
          offsetX: 0,
          offsetY: 0,
        };
        
        needsRedrawRef.current = true;
      }
    };
    
    return () => {
      imageRef.current = null;
    };
  }, [imageUrl, imageSize, calculateImageScale]);

  // Handle canvas resize
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      
      if (!canvas || !container) return;
      
      // Set canvas size to match container
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      
      // Recalculate image scale
      if (imageRef.current) {
        imageScaleRef.current = calculateImageScale(
          canvas.width,
          canvas.height,
          imageSize.width,
          imageSize.height
        );
      }
      
      needsRedrawRef.current = true;
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    
    return () => window.removeEventListener('resize', handleResize);
  }, [imageSize, calculateImageScale]);

  // Start animation loop
  useEffect(() => {
    rafIdRef.current = requestAnimationFrame(animate);
    
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [animate]);

  // Mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const transform = transformRef.current;
    const oldScale = transform.scale;
    
    // Zoom factor
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const newScale = Math.max(0.1, Math.min(10, oldScale * zoomFactor));
    
    // Zoom towards mouse position
    const scaleChange = newScale / oldScale;
    transform.offsetX = mouseX - (mouseX - transform.offsetX) * scaleChange;
    transform.offsetY = mouseY - (mouseY - transform.offsetY) * scaleChange;
    transform.scale = newScale;
    
    needsRedrawRef.current = true;
  }, []);

  // Mouse down - start panning
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    isPanningRef.current = true;
    lastPanPointRef.current = { x: e.clientX, y: e.clientY };
    
    if (canvasRef.current) {
      canvasRef.current.style.cursor = 'grabbing';
    }
  }, []);

  // Mouse move - pan or hover detection (optimized with throttling)
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Handle panning
    if (isPanningRef.current) {
      const dx = e.clientX - lastPanPointRef.current.x;
      const dy = e.clientY - lastPanPointRef.current.y;
      
      transformRef.current.offsetX += dx;
      transformRef.current.offsetY += dy;
      
      lastPanPointRef.current = { x: e.clientX, y: e.clientY };
      needsRedrawRef.current = true;
      return;
    }
    
    // Handle hover detection (throttled)
    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;
    
    // Convert to image coordinates
    const imageCoords = canvasToImage(canvasX, canvasY);
    
    // Check if mouse is over any bounding box (use validDetections)
    let foundHover = false;
    for (let i = 0; i < validDetections.length; i++) {
      const bbox = validDetections[i].bbox;
      
      if (
        imageCoords.x >= bbox.x1 &&
        imageCoords.x <= bbox.x2 &&
        imageCoords.y >= bbox.y1 &&
        imageCoords.y <= bbox.y2
      ) {
        const nodeId = `node_${i}`;
        if (hoveredNodeIdRef.current !== nodeId) {
          setHoveredNodeId(nodeId);
        }
        foundHover = true;
        canvas.style.cursor = 'pointer';
        break;
      }
    }
    
    if (!foundHover) {
      if (hoveredNodeIdRef.current !== null) {
        setHoveredNodeId(null);
      }
      canvas.style.cursor = 'grab';
    }
  }, [validDetections, canvasToImage, setHoveredNodeId]);

  // Mouse up - stop panning
  const handleMouseUp = useCallback(() => {
    isPanningRef.current = false;
    
    if (canvasRef.current) {
      canvasRef.current.style.cursor = 'grab';
    }
  }, []);

  // Mouse click - select detection (optimized)
  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const canvasX = e.clientX - rect.left;
    const canvasY = e.clientY - rect.top;
    
    // Convert to image coordinates
    const imageCoords = canvasToImage(canvasX, canvasY);
    
    // Check if click is on any bounding box (use validDetections)
    for (let i = 0; i < validDetections.length; i++) {
      const bbox = validDetections[i].bbox;
      
      if (
        imageCoords.x >= bbox.x1 &&
        imageCoords.x <= bbox.x2 &&
        imageCoords.y >= bbox.y1 &&
        imageCoords.y <= bbox.y2
      ) {
        const nodeId = `node_${i}`;
        setSelectedNodeId(nodeId);
        return;
      }
    }
    
    // Click on empty space - deselect
    setSelectedNodeId(null);
  }, [validDetections, canvasToImage, setSelectedNodeId]);

  // Zoom to selected detection (optimized)
  useEffect(() => {
    if (!selectedNodeId || !canvasRef.current) return;
    
    const index = parseInt(selectedNodeId.replace('node_', ''));
    if (index < 0 || index >= validDetections.length) return;
    
    const detection = validDetections[index];
    if (!detection?.bbox) return;
    
    const bbox = detection.bbox;
    const canvas = canvasRef.current;
    const scale = imageScaleRef.current;
    
    // Calculate center of bounding box in canvas coordinates
    const centerX = ((bbox.x1 + bbox.x2) / 2) * scale.uniformScale + scale.marginX;
    const centerY = ((bbox.y1 + bbox.y2) / 2) * scale.uniformScale + scale.marginY;
    
    // Calculate zoom level
    const bboxWidth = (bbox.x2 - bbox.x1) * scale.uniformScale;
    const bboxHeight = (bbox.y2 - bbox.y1) * scale.uniformScale;
    const targetSize = Math.max(bboxWidth, bboxHeight) * 3;
    
    const scaleX = canvas.width / targetSize;
    const scaleY = canvas.height / targetSize;
    const newScale = Math.min(scaleX, scaleY, 4);
    
    // Animate to new position
    const startTransform = { ...transformRef.current };
    const targetTransform = {
      scale: newScale,
      offsetX: canvas.width / 2 - centerX * newScale,
      offsetY: canvas.height / 2 - centerY * newScale,
    };
    
    const duration = 600;
    const startTime = performance.now();
    
    const animateZoom = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Ease in-out cubic
      const eased = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;
      
      transformRef.current = {
        scale: startTransform.scale + (targetTransform.scale - startTransform.scale) * eased,
        offsetX: startTransform.offsetX + (targetTransform.offsetX - startTransform.offsetX) * eased,
        offsetY: startTransform.offsetY + (targetTransform.offsetY - startTransform.offsetY) * eased,
      };
      
      needsRedrawRef.current = true;
      
      if (progress < 1) {
        requestAnimationFrame(animateZoom);
      }
    };
    
    requestAnimationFrame(animateZoom);
  }, [selectedNodeId, validDetections]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-industrial-900 rounded-lg overflow-hidden relative"
    >
      <canvas
        ref={canvasRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
        className="w-full h-full"
        style={{ cursor: 'grab' }}
      />
      
      {/* Controls Overlay */}
      <div className="absolute bottom-4 right-4 bg-industrial-800/90 backdrop-blur-sm rounded-lg p-3 border border-industrial-600 pointer-events-none">
        <div className="text-xs text-industrial-300 space-y-1 font-mono">
          <div>🖱️ Drag to pan</div>
          <div>🔍 Scroll to zoom</div>
          <div>📍 Click box to select</div>
          <div className="pt-2 border-t border-industrial-600">
            Zoom: {(transformRef.current.scale * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
};
