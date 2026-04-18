// Professional P&ID Topology Graph Viewer
// Maintains exact spatial relationships from original P&ID
import React, { useCallback, useMemo, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
  MarkerType,
  useReactFlow,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useAppStore } from '@/store/useAppStore';
import type { GraphData } from '@/types/api';
import { AlertCircle, Maximize2, ZoomIn, ZoomOut } from 'lucide-react';

interface GraphViewerProps {
  graphData: GraphData;
}

export const GraphViewer: React.FC<GraphViewerProps> = ({ graphData }) => {
  const { selectedNodeId, setSelectedNodeId } = useAppStore();
  const [error, setError] = useState<string | null>(null);
  const { fitView: triggerFitView, zoomIn, zoomOut } = useReactFlow();
  const [editMode, setEditMode] = useState(false);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isReady, setIsReady] = useState(false);
  
  // Smart OCR Tag Explainer state
  const [tagAnalysis, setTagAnalysis] = useState<{
    tag: string;
    definition: string;
  } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Transform backend graph data maintaining EXACT P&ID spatial relationships
  const { initialNodes, initialEdges } = useMemo(() => {
    try {
      // Validate graph data
      if (!graphData || !graphData.nodes || !Array.isArray(graphData.nodes)) {
        throw new Error('Invalid graph data: nodes array is missing');
      }

      if (!graphData.edges || !Array.isArray(graphData.edges)) {
        console.warn('No edges found in graph data');
      }

      console.log('=== GRAPH RENDERING ===');
      console.log('Total nodes:', graphData.nodes.length);
      console.log('Total edges:', graphData.edges.length);
      
      // Log first few nodes to see raw data
      console.log('Sample raw nodes:', graphData.nodes.slice(0, 3));

      // Extract valid coordinates
      const coords = graphData.nodes
        .filter(n => n.x !== undefined && n.y !== undefined && n.id)
        .map(n => ({ x: n.x, y: n.y, id: n.id }));

      if (coords.length === 0) {
        throw new Error('No valid coordinates found in graph data');
      }

      // Calculate bounds with padding
      const xValues = coords.map(c => c.x);
      const yValues = coords.map(c => c.y);
      
      const minX = Math.min(...xValues);
      const maxX = Math.max(...xValues);
      const minY = Math.min(...yValues);
      const maxY = Math.max(...yValues);
      
      const rangeX = maxX - minX || 1;
      const rangeY = maxY - minY || 1;
      
      console.log('Original Bounds:', { minX, maxX, minY, maxY });
      console.log('Original Ranges:', { rangeX, rangeY });

      // Simple transformation: just normalize to start from (0,0)
      // Don't scale - use coordinates as-is from backend
      // Backend should be sending pixel coordinates from the original P&ID image
      const positions = new Map<string, { x: number; y: number }>();
      
      coords.forEach(coord => {
        // Simply shift coordinates to start from (0,0)
        const finalX = coord.x - minX;
        const finalY = coord.y - minY;
        positions.set(coord.id, { x: finalX, y: finalY });
      });
      
      console.log('Transformed coordinate range:', { 
        x: `0 to ${rangeX.toFixed(1)}`,
        y: `0 to ${rangeY.toFixed(1)}`
      });
      console.log('First 3 transformed positions:', 
        Array.from(positions.entries()).slice(0, 3).map(([id, pos]) => 
          `${id}: (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})`
        )
      );
      
      // Warn if coordinates seem clustered
      if (rangeX < 500 || rangeY < 500) {
        console.warn('⚠️ WARNING: Coordinates appear clustered!');
        console.warn(`   Range: ${rangeX.toFixed(1)} x ${rangeY.toFixed(1)} pixels`);
        console.warn('   This indicates a backend detection issue.');
        console.warn('   Nodes will appear clustered in the graph.');
      }

      // Create nodes with exact positions
      const nodes: Node[] = graphData.nodes
        .filter((node) => {
          if (!node.id) {
            console.warn('Skipping node without id:', node);
            return false;
          }
          if (!positions.has(node.id)) {
            console.warn('Skipping node without position:', node.id);
            return false;
          }
          return true;
        })
        .map((node) => {
          const position = positions.get(node.id)!;
          const nodeType = getNodeType(node.type);
          const color = getNodeColor(node.type);
          
          const isCircle = nodeType.shape === 'default';
          const nodeWidth = isCircle ? 60 : 100;
          const nodeHeight = isCircle ? 60 : 50;
          
          return {
            id: node.id,
            type: nodeType.shape,
            position: {
              x: position.x,
              y: position.y
            },
            data: {
              label: node.tag || node.label || node.id,
              type: node.type,
            },
            measured: {
              width: nodeWidth,
              height: nodeHeight,
            },
            width: nodeWidth,
            height: nodeHeight,
            style: {
              background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
              color: '#ffffff',
              border: `2px solid ${color}`,
              borderRadius: isCircle ? '50%' : '6px',
              padding: 8,
              fontSize: 9,
              fontWeight: 600,
              fontFamily: 'monospace',
              width: nodeWidth,
              height: nodeHeight,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 2px 6px ${color}40`,
              textAlign: 'center',
              wordBreak: 'break-word',
              cursor: 'pointer',
            },
          };
        });

      console.log('Created nodes:', nodes.length);
      console.log('First 3 node positions:', nodes.slice(0, 3).map(n => ({ 
        id: n.id, 
        x: n.position.x.toFixed(1), 
        y: n.position.y.toFixed(1),
        width: n.width,
        height: n.height
      })));

      // Create edges
      const edges: Edge[] = (graphData.edges || [])
        .filter((edge) => {
          if (!edge.source || !edge.target) return false;
          const sourceExists = nodes.some(n => n.id === edge.source);
          const targetExists = nodes.some(n => n.id === edge.target);
          return sourceExists && targetExists;
        })
        .map((edge, index) => {
          const edgeColor = getEdgeColor(edge.type);
          
          return {
            id: `edge-${index}`,
            source: edge.source,
            target: edge.target,
            type: ConnectionLineType.SmoothStep,
            animated: edge.type === 'flow',
            style: {
              stroke: edgeColor,
              strokeWidth: 2,
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: edgeColor,
              width: 20,
              height: 20,
            },
            label: edge.type,
            labelStyle: {
              fill: '#abb2bf',
              fontSize: 10,
              fontWeight: 600,
              fontFamily: 'monospace',
            },
            labelBgStyle: {
              fill: '#1a1f29',
              fillOpacity: 0.9,
            },
          };
        });

      console.log('Created edges:', edges.length);
      console.log('=== GRAPH RENDERING COMPLETE ===');

      if (nodes.length === 0) {
        throw new Error('No valid nodes found');
      }

      setError(null);
      return { initialNodes: nodes, initialEdges: edges };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Error processing graph:', err);
      setError(errorMessage);
      return { initialNodes: [], initialEdges: [] };
    }
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when initialNodes change
  useEffect(() => {
    console.log('=== UPDATING NODES ===');
    console.log('Setting', initialNodes.length, 'nodes');
    console.log('Sample node structure:', initialNodes[0]);
    console.log('All node positions:', initialNodes.map(n => ({
      id: n.id,
      x: n.position.x,
      y: n.position.y,
      width: n.width,
      height: n.height
    })).slice(0, 5));
    setNodes(initialNodes);
    setIsReady(false);
  }, [initialNodes, setNodes]);

  // Update edges when initialEdges change
  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Robust auto-fit: wait for ReactFlow to be fully initialized
  useEffect(() => {
    if (nodes.length === 0) return;
    
    setIsInitializing(true);
    
    // Use requestAnimationFrame to ensure DOM is ready
    const fitGraph = () => {
      requestAnimationFrame(() => {
        triggerFitView({ 
          padding: 0.2,
          duration: 0,
          minZoom: 0.1,
          maxZoom: 1.0,
        });
        
        // Second fit after a delay to ensure all nodes are rendered
        setTimeout(() => {
          triggerFitView({ 
            padding: 0.2,
            duration: 400,
            minZoom: 0.1,
            maxZoom: 1.0,
          });
          setIsInitializing(false);
          setIsReady(true);
        }, 300);
      });
    };
    
    // Small delay to let ReactFlow initialize
    const timer = setTimeout(fitGraph, 100);
    
    return () => clearTimeout(timer);
  }, [nodes.length, triggerFitView]);

  // Handle node click
  const onNodeClick = useCallback(
    async (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
      
      // If it's an instrument node, trigger AI analysis
      if (node.data.type?.toLowerCase().includes('instrument')) {
        // Get the actual tag from the label, or use node ID if label is generic
        const tagLabel = node.data.label;
        
        // Skip analysis if label is just the class name
        if (tagLabel && !tagLabel.includes('.') && tagLabel !== 'UNTAGGED') {
          await analyzeTag(tagLabel);
        } else {
          // Show message that tag is not available
          setTagAnalysis({
            tag: node.id,
            definition: "No instrument tag found. This node needs to be tagged with an ISA instrument identifier (e.g., FIC-101, PT-205)."
          });
        }
      } else {
        // Clear analysis for non-instrument nodes
        setTagAnalysis(null);
        setAnalysisError(null);
      }
    },
    [setSelectedNodeId]
  );
  
  // Analyze tag using Gemini AI
  const analyzeTag = async (tagLabel: string) => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    setTagAnalysis(null);
    
    try {
      // Create form data (mocking image upload for now)
      const formData = new FormData();
      formData.append('tag_text', tagLabel);
      
      const response = await fetch('/api/api/analyze-tag', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      setTagAnalysis(data);
    } catch (error) {
      console.error('Error analyzing tag:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Failed to analyze tag');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle edge click
  const onEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      if (editMode) {
        setSelectedEdge(edge.id);
      }
    },
    [editMode]
  );

  // Handle fit view
  const handleFitView = useCallback(() => {
    triggerFitView({ 
      padding: 0.2, 
      duration: 400,
      minZoom: 0.1,
      maxZoom: 1.0,
    });
  }, [triggerFitView]);

  // Delete node
  const handleDeleteNode = useCallback(() => {
    if (selectedNodeId) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
      setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
      setSelectedNodeId(null);
    }
  }, [selectedNodeId, setNodes, setEdges, setSelectedNodeId]);

  // Delete edge
  const handleDeleteEdge = useCallback(() => {
    if (selectedEdge) {
      setEdges((eds) => eds.filter((e) => e.id !== selectedEdge));
      setSelectedEdge(null);
    }
  }, [selectedEdge, setEdges]);

  // Highlight selected node
  useEffect(() => {
    if (nodes.length === 0) return;
    
    setNodes((nds) =>
      nds.map((node) => {
        const border = node.style?.border;
        const borderColor = typeof border === 'string' ? border.split(' ')[2] : '#61afef';
        const isSelected = selectedNodeId === node.id;
        
        return {
          ...node,
          style: {
            ...node.style,
            // Only update boxShadow and zIndex
            // ❌ DO NOT USE 'transform' or 'transition' HERE
            // It overrides React Flow's internal position translates!
            boxShadow: isSelected
              ? `0 0 20px ${borderColor}, 0 0 40px ${borderColor}80`
              : `0 2px 6px ${borderColor}40`,
            zIndex: isSelected ? 1000 : 1,
          },
        };
      })
    );
  }, [selectedNodeId, setNodes, nodes.length]);

  // Error state
  if (error) {
    return (
      <div className="w-full h-full bg-industrial-900 rounded-lg border border-industrial-600 flex items-center justify-center">
        <div className="text-center p-8">
          <AlertCircle className="w-16 h-16 text-accent-red mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-industrial-200 mb-2">
            Graph Error
          </h3>
          <p className="text-sm text-industrial-400 mb-4">{error}</p>
          <p className="text-xs text-industrial-500">
            Please process a P&ID image first.
          </p>
        </div>
      </div>
    );
  }

  // Empty state
  if (initialNodes.length === 0) {
    return (
      <div className="w-full h-full bg-industrial-900 rounded-lg border border-industrial-600 flex items-center justify-center">
        <div className="text-center p-8">
          <AlertCircle className="w-16 h-16 text-industrial-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-industrial-200 mb-2">
            No Graph Data
          </h3>
          <p className="text-sm text-industrial-400">
            Upload and process a P&ID image to view the graph.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-industrial-900 rounded-lg border border-industrial-600 relative">
      {/* Loading Overlay */}
      {isInitializing && (
        <div className="absolute inset-0 bg-industrial-950/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-industrial-300 text-sm font-mono">Fitting graph to view...</p>
          </div>
        </div>
      )}
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        nodesDraggable={true}
        nodesConnectable={editMode}
        elementsSelectable={true}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: false,
          minZoom: 0.1,
          maxZoom: 1.0,
        }}
        minZoom={0.05}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
        attributionPosition="bottom-left"
        className="bg-industrial-950"
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#3d4556" gap={16} size={1} />
        
        <Controls
          className="bg-industrial-800/90 border border-industrial-600 rounded-lg"
          position="top-left"
          showInteractive={false}
        />
        
        <MiniMap
          key={`minimap-${nodes.length}`}
          nodeColor={(node) => {
            const border = node.style?.border;
            const borderColor = typeof border === 'string' ? border.split(' ')[2] : '#61afef';
            return borderColor || '#61afef';
          }}
          nodeStrokeWidth={3}
          nodeStrokeColor="#ffffff"
          nodeBorderRadius={2}
          className="bg-industrial-800/90 border border-industrial-600 rounded-lg"
          maskColor="rgba(10, 14, 20, 0.6)"
          position="bottom-right"
          pannable
          zoomable
          style={{ width: 200, height: 150 }}
        />

        {/* Top Right Panel */}
        <Panel position="top-right" className="space-y-2">
          {/* Edit Mode */}
          <div className="bg-industrial-800/95 backdrop-blur-sm rounded-lg border border-industrial-600 shadow-xl p-3">
            <h3 className="text-xs font-bold text-industrial-200 mb-2 font-mono">
              Edit Mode
            </h3>
            <button
              onClick={() => setEditMode(!editMode)}
              className={`w-full px-3 py-2 text-xs rounded transition-colors font-semibold ${
                editMode
                  ? 'bg-accent-green text-industrial-950'
                  : 'bg-industrial-700 text-industrial-300 hover:bg-industrial-600'
              }`}
            >
              {editMode ? '✓ Editing' : 'Enable Edit'}
            </button>
            {editMode && (
              <div className="mt-2 space-y-1">
                <button
                  onClick={handleDeleteNode}
                  disabled={!selectedNodeId}
                  className="w-full px-2 py-1.5 text-xs rounded bg-accent-red hover:bg-accent-red/80 disabled:bg-industrial-700 disabled:text-industrial-500 text-industrial-950 font-semibold transition-colors"
                >
                  Delete Node
                </button>
                <button
                  onClick={handleDeleteEdge}
                  disabled={!selectedEdge}
                  className="w-full px-2 py-1.5 text-xs rounded bg-accent-red hover:bg-accent-red/80 disabled:bg-industrial-700 disabled:text-industrial-500 text-industrial-950 font-semibold transition-colors"
                >
                  Delete Edge
                </button>
              </div>
            )}
          </div>

          {/* Zoom Controls */}
          <div className="bg-industrial-800/95 backdrop-blur-sm rounded-lg border border-industrial-600 shadow-xl">
            <button
              onClick={() => zoomIn({ duration: 200 })}
              className="w-full px-3 py-2 hover:bg-industrial-700 transition-colors border-b border-industrial-600"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4 text-industrial-300 mx-auto" />
            </button>
            <button
              onClick={() => zoomOut({ duration: 200 })}
              className="w-full px-3 py-2 hover:bg-industrial-700 transition-colors border-b border-industrial-600"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4 text-industrial-300 mx-auto" />
            </button>
            <button
              onClick={handleFitView}
              className="w-full px-3 py-2 hover:bg-industrial-700 transition-colors"
              title="Fit View"
            >
              <Maximize2 className="w-4 h-4 text-industrial-300 mx-auto" />
            </button>
          </div>

          {/* Stats */}
          <div className="bg-industrial-800/95 backdrop-blur-sm rounded-lg p-3 border border-industrial-600 shadow-xl max-w-xs">
            <h3 className="text-xs font-bold text-industrial-200 mb-2 font-mono">
              Graph Stats
            </h3>
            <div className="text-xs space-y-1">
              <div className="flex justify-between gap-3">
                <span className="text-industrial-400">Nodes:</span>
                <span className="text-industrial-200 font-mono font-semibold">{nodes.length}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-industrial-400">Edges:</span>
                <span className="text-industrial-200 font-mono font-semibold">{edges.length}</span>
              </div>
              {isReady && (
                <div className="pt-1 border-t border-industrial-700">
                  <span className="text-accent-green text-xs">✓ Ready</span>
                  <div className="mt-1 text-[10px] text-industrial-500">
                    Check browser console for coordinate details
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Smart OCR Tag Explainer */}
          {selectedNodeId && (
            <div className="bg-industrial-800/95 backdrop-blur-sm rounded-lg p-3 border border-industrial-600 shadow-xl max-w-xs">
              <h3 className="text-xs font-bold text-industrial-200 mb-2 font-mono flex items-center gap-2">
                <span className="text-accent-blue">🤖</span>
                AI Tag Explainer
              </h3>
              
              {isAnalyzing ? (
                <div className="flex flex-col items-center justify-center py-4">
                  <div className="w-8 h-8 border-3 border-accent-blue border-t-transparent rounded-full animate-spin mb-2" />
                  <p className="text-xs text-industrial-400">Analyzing tag...</p>
                </div>
              ) : analysisError ? (
                <div className="text-xs text-accent-red bg-accent-red/10 rounded p-2">
                  <p className="font-semibold mb-1">⚠️ API Error</p>
                  <p className="text-[10px]">{analysisError}</p>
                </div>
              ) : tagAnalysis ? (
                <div className="space-y-2">
                  <div className="bg-industrial-900/50 rounded p-2">
                    <p className="text-[10px] text-industrial-400 mb-1">Tag</p>
                    <p className="text-sm font-bold text-accent-blue font-mono break-all">
                      {tagAnalysis.tag}
                    </p>
                  </div>
                  <div className="bg-industrial-900/50 rounded p-2">
                    <p className="text-[10px] text-industrial-400 mb-1">Definition</p>
                    <p className="text-xs text-industrial-200 leading-relaxed">
                      {tagAnalysis.definition}
                    </p>
                  </div>
                  {tagAnalysis.definition.includes('⚠️') && (
                    <div className="text-[10px] text-accent-yellow bg-accent-yellow/10 rounded p-2 mt-2">
                      <p className="font-semibold">💡 Tip</p>
                      <p>This node needs proper ISA tag extraction from the P&ID image.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs text-industrial-400 text-center py-3">
                  Click an instrument node to analyze its tag
                </div>
              )}
            </div>
          )}
        </Panel>

        {/* Bottom Left Panel - Legend */}
        <Panel position="bottom-left" className="mb-2 ml-2">
          <div className="bg-industrial-800/95 backdrop-blur-sm rounded-lg p-3 border border-industrial-600 shadow-xl">
            <h3 className="text-xs font-bold text-industrial-200 mb-2 font-mono">
              Legend
            </h3>
            <div className="space-y-1.5 text-xs">
              <LegendItem color="#61afef" shape="circle" label="Instruments" />
              <LegendItem color="#56b6c2" shape="circle" label="Valves" />
              <LegendItem color="#98c379" shape="square" label="Equipment" />
              <LegendItem color="#e5c07b" shape="square" label="Pumps" />
              <LegendItem color="#c678dd" shape="square" label="Other" />
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
};

// Helper Components
const LegendItem: React.FC<{
  color: string;
  shape: 'circle' | 'square';
  label: string;
}> = ({ color, shape, label }) => (
  <div className="flex items-center gap-2">
    <div
      className={`w-3 h-3 border-2 ${
        shape === 'circle' ? 'rounded-full' : 'rounded'
      }`}
      style={{ borderColor: color, backgroundColor: `${color}40` }}
    />
    <span className="text-industrial-300 font-mono text-xs">{label}</span>
  </div>
);

// Helper Functions
const getNodeType = (
  type: string
): { shape: 'default' | 'input' | 'output' } => {
  const lowerType = type.toLowerCase();
  if (lowerType.includes('instrument') || lowerType.includes('valve')) {
    return { shape: 'default' }; // Circle
  }
  return { shape: 'input' }; // Rectangle
};

const getNodeColor = (type: string): string => {
  const lowerType = type.toLowerCase();
  if (lowerType.includes('instrument')) return '#61afef';
  if (lowerType.includes('valve')) return '#56b6c2';
  if (lowerType.includes('equipment')) return '#98c379';
  if (lowerType.includes('pump')) return '#e5c07b';
  return '#c678dd';
};

const getEdgeColor = (type: string): string => {
  if (type === 'flow') return '#98c379';
  if (type === 'signal') return '#61afef';
  if (type === 'control') return '#e5c07b';
  return '#828997';
};
