// Feature 1: Interactive Pan/Zoom Canvas with Bounding Boxes
import React, { useRef, useEffect, useState } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect, Text, Group } from 'react-konva';
import { useAppStore } from '@/store/useAppStore';
import type { DetectionResult } from '@/types/api';

interface InteractiveCanvasProps {
  imageUrl: string;
  detections: DetectionResult[];
  imageSize: { width: number; height: number };
}

export const InteractiveCanvas: React.FC<InteractiveCanvasProps> = ({
  imageUrl,
  detections,
  imageSize,
}) => {
  const stageRef = useRef<any>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [stageSize, setStageSize] = useState({ width: 1200, height: 800 });
  const [stageScale, setStageScale] = useState(1);
  const [stagePos, setStagePos] = useState({ x: 0, y: 0 });
  
  const { selectedNodeId, hoveredNodeId, setHoveredNodeId, setSelectedNodeId } = useAppStore();

  // Load image
  useEffect(() => {
    const img = new window.Image();
    img.src = imageUrl;
    img.onload = () => {
      setImage(img);
      // Fit image to canvas
      const scale = Math.min(
        stageSize.width / imageSize.width,
        stageSize.height / imageSize.height
      ) * 0.9;
      setStageScale(scale);
      setStagePos({
        x: (stageSize.width - imageSize.width * scale) / 2,
        y: (stageSize.height - imageSize.height * scale) / 2,
      });
    };
  }, [imageUrl, imageSize, stageSize]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const container = document.getElementById('canvas-container');
      if (container) {
        setStageSize({
          width: container.offsetWidth,
          height: container.offsetHeight,
        });
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Zoom to specific detection (called from table click)
  useEffect(() => {
    if (selectedNodeId && stageRef.current && detections.length > 0) {
      const index = parseInt(selectedNodeId.replace('node_', ''));
      
      if (index >= 0 && index < detections.length) {
        const detection = detections[index];
        
        if (detection && detection.bbox) {
          const bbox = detection.bbox;
          
          // Calculate center of bounding box
          const centerX = (bbox.x1 + bbox.x2) / 2;
          const centerY = (bbox.y1 + bbox.y2) / 2;
          
          // Calculate zoom level to fit the detection nicely
          const bboxWidth = bbox.x2 - bbox.x1;
          const bboxHeight = bbox.y2 - bbox.y1;
          const targetSize = Math.max(bboxWidth, bboxHeight) * 3; // Show 3x the detection size
          
          const scaleX = stageSize.width / targetSize;
          const scaleY = stageSize.height / targetSize;
          const newScale = Math.min(scaleX, scaleY, 4); // Max 4x zoom
          
          // Calculate position to center the detection
          const newPos = {
            x: stageSize.width / 2 - centerX * newScale,
            y: stageSize.height / 2 - centerY * newScale,
          };
          
          // Smooth animation
          const stage = stageRef.current;
          stage.to({
            x: newPos.x,
            y: newPos.y,
            scaleX: newScale,
            scaleY: newScale,
            duration: 0.6,
            easing: (t: number) => {
              // easeInOutCubic for smoother animation
              return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
            },
          });
          
          // Update state after animation
          setTimeout(() => {
            setStageScale(newScale);
            setStagePos(newPos);
          }, 600);
        }
      }
    }
  }, [selectedNodeId, detections, stageSize]);

  // Handle wheel zoom - ONLY when mouse is over canvas
  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    e.evt.stopPropagation();
    
    const stage = stageRef.current;
    if (!stage) return;
    
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();
    
    if (!pointer) return;
    
    const scaleBy = 1.1;
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;
    
    // Limit zoom
    const clampedScale = Math.max(0.1, Math.min(10, newScale));
    
    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };
    
    const newPos = {
      x: pointer.x - mousePointTo.x * clampedScale,
      y: pointer.y - mousePointTo.y * clampedScale,
    };
    
    setStageScale(clampedScale);
    setStagePos(newPos);
  };

  // Get color based on class
  const getClassColor = (className: string): string => {
    if (className.includes('instrument')) return '#61afef';
    if (className.includes('valve')) return '#56b6c2';
    if (className.includes('equipment')) return '#98c379';
    if (className.includes('pump')) return '#e5c07b';
    return '#c678dd';
  };

  return (
    <div 
      id="canvas-container" 
      className="w-full h-full bg-industrial-900 rounded-lg overflow-hidden relative"
      onWheel={(e) => {
        // Prevent scroll propagation to parent
        e.stopPropagation();
      }}
    >
      <Stage
        ref={stageRef}
        width={stageSize.width}
        height={stageSize.height}
        scaleX={stageScale}
        scaleY={stageScale}
        x={stagePos.x}
        y={stagePos.y}
        draggable
        onWheel={handleWheel}
        onDragEnd={(e) => {
          setStagePos({ x: e.target.x(), y: e.target.y() });
        }}
      >
        <Layer>
          {/* Background Image */}
          {image && (
            <KonvaImage
              image={image}
              width={imageSize.width}
              height={imageSize.height}
            />
          )}
          
          {/* Bounding Boxes */}
          {detections.map((detection, index) => {
            const nodeId = `node_${index}`;
            const isSelected = selectedNodeId === nodeId;
            const isHovered = hoveredNodeId === nodeId;
            const bbox = detection.bbox;
            const color = getClassColor(detection.class_name);
            
            return (
              <Group
                key={nodeId}
                onMouseEnter={() => setHoveredNodeId(nodeId)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onClick={() => setSelectedNodeId(nodeId)}
              >
                {/* Bounding Box */}
                <Rect
                  x={bbox.x1}
                  y={bbox.y1}
                  width={bbox.x2 - bbox.x1}
                  height={bbox.y2 - bbox.y1}
                  stroke={color}
                  strokeWidth={isSelected ? 4 : isHovered ? 3 : 2}
                  shadowBlur={isSelected || isHovered ? 10 : 0}
                  shadowColor={color}
                  listening={true}
                />
                
                {/* Tag Label */}
                {detection.tag && (
                  <Group>
                    <Rect
                      x={bbox.x1}
                      y={bbox.y1 - 25}
                      width={(detection.tag.length * 8) + 10}
                      height={20}
                      fill={color}
                      opacity={0.9}
                      cornerRadius={3}
                    />
                    <Text
                      x={bbox.x1 + 5}
                      y={bbox.y1 - 22}
                      text={detection.tag}
                      fontSize={14}
                      fontFamily="monospace"
                      fill="#0a0e14"
                      fontStyle="bold"
                    />
                  </Group>
                )}
                
                {/* Hover Tooltip */}
                {isHovered && (
                  <Group>
                    <Rect
                      x={bbox.x2 + 10}
                      y={bbox.y1}
                      width={200}
                      height={80}
                      fill="#1a1f29"
                      stroke={color}
                      strokeWidth={2}
                      cornerRadius={8}
                      shadowBlur={15}
                      shadowColor={color}
                      opacity={0.95}
                    />
                    <Text
                      x={bbox.x2 + 20}
                      y={bbox.y1 + 10}
                      text={`Tag: ${detection.tag || 'N/A'}`}
                      fontSize={13}
                      fill="#abb2bf"
                      fontFamily="monospace"
                    />
                    <Text
                      x={bbox.x2 + 20}
                      y={bbox.y1 + 30}
                      text={`Class: ${detection.class_name}`}
                      fontSize={12}
                      fill="#828997"
                      fontFamily="monospace"
                    />
                    <Text
                      x={bbox.x2 + 20}
                      y={bbox.y1 + 50}
                      text={`Confidence: ${(detection.confidence * 100).toFixed(1)}%`}
                      fontSize={12}
                      fill={color}
                      fontFamily="monospace"
                      fontStyle="bold"
                    />
                  </Group>
                )}
              </Group>
            );
          })}
        </Layer>
      </Stage>
      
      {/* Controls Overlay */}
      <div className="absolute bottom-4 right-4 bg-industrial-800/90 backdrop-blur-sm rounded-lg p-3 border border-industrial-600">
        <div className="text-xs text-industrial-300 space-y-1 font-mono">
          <div>🖱️ Drag to pan</div>
          <div>🔍 Scroll to zoom</div>
          <div>📍 Click box to select</div>
          <div className="pt-2 border-t border-industrial-600">
            Zoom: {(stageScale * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
};
