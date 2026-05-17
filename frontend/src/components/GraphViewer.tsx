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
import { AlertCircle, Maximize2, ZoomIn, ZoomOut, Wrench, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Filter, X } from 'lucide-react';
import { ChatPanel } from './ChatPanel';
import { GraphFilter } from './GraphFilter';
import { MaintenanceChecklist } from './MaintenanceChecklist';

interface GraphViewerProps {
  graphData: GraphData;
}

export const GraphViewer: React.FC<GraphViewerProps> = ({ graphData }) => {
  const { selectedNodeId, setSelectedNodeId, flowSimulationResult } = useAppStore();
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
  
  // Graph Filter state
  const [isFilterActive, setIsFilterActive] = useState(false);
  const [filteredNodeIds, setFilteredNodeIds] = useState<string[]>([]);
  const [filteredEdgeIds, setFilteredEdgeIds] = useState<string[]>([]);
  
  // Maintenance Checklist state
  const [showMaintenanceChecklist, setShowMaintenanceChecklist] = useState(false);
  const [selectedEquipment, setSelectedEquipment] = useState<{
    type: string;
    tag: string;
    description: string;
  } | null>(null);
  
  // Panel collapse state
  const [isFilterCollapsed, setIsFilterCollapsed] = useState(false);
  const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(false);
  const [isLegendCollapsed, setIsLegendCollapsed] = useState(true);

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
          const edgeId = `${edge.source}-${edge.target}`;
          
          // Check if this edge is active in flow simulation
          const isActiveInFlow = flowSimulationResult?.active_edge_ids.includes(edgeId) || false;
          
          return {
            id: `edge-${index}`,
            source: edge.source,
            target: edge.target,
            type: ConnectionLineType.SmoothStep,
            animated: isActiveInFlow, // Animate if active in flow
            style: {
              stroke: isActiveInFlow ? '#98c379' : edgeColor, // Green for active flow
              strokeWidth: isActiveInFlow ? 4 : 2, // Thicker for active flow
              opacity: flowSimulationResult && !isActiveInFlow ? 0.3 : 1, // Dim inactive edges
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: isActiveInFlow ? '#98c379' : edgeColor,
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
  }, [graphData, flowSimulationResult]);

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
      
      // Store equipment info for maintenance checklist
      setSelectedEquipment({
        type: node.data.type || 'Equipment',
        tag: node.data.label || node.id,
        description: `${node.data.type || 'Equipment'} node from P&ID`
      });
      
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

  // Handle filter applied
  const handleFilterApplied = useCallback((matchedNodeIds: string[], matchedEdgeIds: string[]) => {
    setIsFilterActive(true);
    setFilteredNodeIds(matchedNodeIds);
    setFilteredEdgeIds(matchedEdgeIds);
  }, []);
  
  // Handle filter cleared
  const handleFilterCleared = useCallback(() => {
    setIsFilterActive(false);
    setFilteredNodeIds([]);
    setFilteredEdgeIds([]);
  }, []);
  
  // Highlight selected node and apply filter dimming + flow simulation highlighting
  useEffect(() => {
    if (nodes.length === 0) return;
    
    setNodes((nds) =>
      nds.map((node) => {
        const border = node.style?.border;
        const borderColor = typeof border === 'string' ? border.split(' ')[2] : '#61afef';
        const isSelected = selectedNodeId === node.id;
        const isFiltered = isFilterActive && !filteredNodeIds.includes(node.id);
        
        // Check if node is active in flow simulation
        const isActiveInFlow = flowSimulationResult?.active_node_ids.includes(node.id) || false;
        const isBlocked = flowSimulationResult?.blocked_nodes.includes(node.id) || false;
        
        // Determine opacity based on filter and flow simulation
        let opacity = 1;
        if (isFiltered) {
          opacity = 0.2;
        } else if (flowSimulationResult && !isActiveInFlow) {
          opacity = 0.3; // Dim inactive nodes when simulation is active
        }
        
        // Determine box shadow based on state
        let boxShadow = `0 2px 6px ${borderColor}40`;
        if (isSelected) {
          boxShadow = `0 0 20px ${borderColor}, 0 0 40px ${borderColor}80`;
        } else if (isBlocked) {
          boxShadow = `0 0 20px #e06c75, 0 0 40px #e06c7580`; // Red glow for blocked
        } else if (isActiveInFlow) {
          boxShadow = `0 0 15px #98c379, 0 0 30px #98c37960`; // Green glow for active flow
        }
        
        return {
          ...node,
          style: {
            ...node.style,
            // Only update boxShadow, zIndex, and opacity
            // ❌ DO NOT USE 'transform' or 'transition' HERE
            // It overrides React Flow's internal position translates!
            boxShadow,
            zIndex: isSelected ? 1000 : isActiveInFlow ? 100 : 1,
            opacity,
          },
        };
      })
    );
  }, [selectedNodeId, isFilterActive, filteredNodeIds, flowSimulationResult, setNodes, nodes.length]);
  
  // Apply filter dimming to edges
  useEffect(() => {
    if (edges.length === 0) return;
    
    setEdges((eds) =>
      eds.map((edge) => {
        const isFiltered = isFilterActive && !filteredEdgeIds.includes(edge.id);
        
        return {
          ...edge,
          style: {
            ...edge.style,
            opacity: isFiltered ? 0.1 : 1,
          },
        };
      })
    );
  }, [isFilterActive, filteredEdgeIds, setEdges, edges.length]);

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
          className="!bg-industrial-800/90 !border-industrial-600 !rounded-xl !shadow-2xl"
          position="bottom-left"
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
          className="!bg-industrial-800/90 !border-industrial-600 !rounded-xl !shadow-2xl"
          maskColor="rgba(10, 14, 20, 0.6)"
          position="bottom-right"
          pannable
          zoomable
          style={{ width: 180, height: 120 }}
        />

        {/* Floating Top Toolbar */}
        <Panel position="top-center" className="flex items-center gap-3">
          {/* Graph Stats Badge */}
          <div className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-full px-4 py-2 shadow-2xl flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
              <span className="text-xs text-industrial-300">Nodes:</span>
              <span className="text-sm font-bold text-accent-blue font-mono">{nodes.length}</span>
            </div>
            <div className="w-px h-4 bg-industrial-600" />
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-accent-cyan" />
              <span className="text-xs text-industrial-300">Edges:</span>
              <span className="text-sm font-bold text-accent-cyan font-mono">{edges.length}</span>
            </div>
            {isReady && (
              <>
                <div className="w-px h-4 bg-industrial-600" />
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-accent-green" />
                  <span className="text-xs text-accent-green font-semibold">Ready</span>
                </div>
              </>
            )}
          </div>

          {/* Flow Simulation Active Indicator */}
          {flowSimulationResult && (
            <div className="bg-gradient-to-r from-accent-green/20 to-accent-green/10 backdrop-blur-md border border-accent-green rounded-full px-4 py-2 shadow-2xl flex items-center gap-2 animate-pulse">
              <div className="w-2 h-2 rounded-full bg-accent-green" />
              <span className="text-xs text-accent-green font-semibold">
                Flow Simulation Active
              </span>
              <span className="text-xs text-accent-green/70 font-mono">
                {flowSimulationResult.active_node_ids.length} nodes
              </span>
            </div>
          )}

          {/* Filter Toggle Button */}
          <button
            onClick={() => setIsFilterCollapsed(!isFilterCollapsed)}
            className={`bg-industrial-800/95 backdrop-blur-md border rounded-full px-4 py-2 shadow-2xl flex items-center gap-2 transition-all hover:scale-105 ${
              isFilterActive 
                ? 'border-accent-blue bg-accent-blue/10' 
                : 'border-industrial-600 hover:border-accent-blue/50'
            }`}
          >
            <Filter className={`w-4 h-4 ${isFilterActive ? 'text-accent-blue' : 'text-industrial-300'}`} />
            <span className={`text-sm font-semibold ${isFilterActive ? 'text-accent-blue' : 'text-industrial-200'}`}>
              {isFilterActive ? 'Filter Active' : 'Smart Filter'}
            </span>
            {isFilterActive && (
              <span className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            )}
          </button>
        </Panel>

        {/* Floating Filter Panel */}
        {!isFilterCollapsed && (
          <Panel position="top-left" className="mt-20 ml-4 animate-slide-in">
            <div className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-2xl shadow-2xl p-4 w-80">
              <GraphFilter
                topology={{ nodes: graphData.nodes, edges: graphData.edges }}
                onFilterApplied={handleFilterApplied}
                onFilterCleared={handleFilterCleared}
              />
            </div>
          </Panel>
        )}

        {/* Floating Node Info Panel */}
        {selectedNodeId && selectedEquipment && (
          <Panel position="top-right" className="mt-20 mr-4 animate-slide-in">
            <div className="bg-gradient-to-br from-industrial-800/95 to-industrial-900/95 backdrop-blur-md border border-accent-blue/30 rounded-2xl shadow-2xl p-4 w-80">
              {/* Node Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-accent-blue/20 border-2 border-accent-blue flex items-center justify-center">
                    <Wrench className="w-5 h-5 text-accent-blue" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-accent-blue font-mono">
                      {selectedEquipment.tag}
                    </h3>
                    <p className="text-xs text-industrial-400">{selectedEquipment.type}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedNodeId(null)}
                  className="p-1.5 hover:bg-industrial-700 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-industrial-400" />
                </button>
              </div>

              {/* Maintenance Button - Hero */}
              <button
                onClick={() => setShowMaintenanceChecklist(true)}
                className="w-full bg-gradient-to-r from-accent-cyan via-accent-blue to-accent-cyan bg-size-200 bg-pos-0 hover:bg-pos-100 text-white font-bold py-3 px-4 rounded-xl shadow-lg hover:shadow-accent-blue/50 transition-all duration-300 flex items-center justify-center gap-2 mb-4"
              >
                <Wrench className="w-5 h-5" />
                <span>Generate Maintenance Checklist</span>
              </button>

              {/* Tag Analysis - Compact */}
              {tagAnalysis && (
                <div className="bg-industrial-900/50 rounded-xl p-3 border border-industrial-700">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-accent-blue/20 flex items-center justify-center">
                      <span className="text-xs">🤖</span>
                    </div>
                    <span className="text-xs font-semibold text-industrial-300">AI Analysis</span>
                  </div>
                  <p className="text-xs text-industrial-400 leading-relaxed line-clamp-3">
                    {tagAnalysis.definition}
                  </p>
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* Floating Legend - Bottom Left */}
        <Panel position="bottom-left" className="mb-20 ml-4">
          <button
            onClick={() => setIsLegendCollapsed(!isLegendCollapsed)}
            className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-full px-4 py-2 shadow-2xl hover:scale-105 transition-all flex items-center gap-2"
          >
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-accent-blue" />
              <div className="w-2 h-2 rounded-full bg-accent-cyan" />
              <div className="w-2 h-2 rounded-full bg-accent-green" />
            </div>
            <span className="text-xs font-semibold text-industrial-200">Legend</span>
            {isLegendCollapsed ? (
              <ChevronUp className="w-3 h-3 text-industrial-400" />
            ) : (
              <ChevronDown className="w-3 h-3 text-industrial-400" />
            )}
          </button>
          
          {!isLegendCollapsed && (
            <div className="mt-2 bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-xl shadow-2xl p-3 animate-slide-in">
              <div className="space-y-2">
                <LegendItem color="#61afef" shape="circle" label="Instruments" />
                <LegendItem color="#56b6c2" shape="circle" label="Valves" />
                <LegendItem color="#98c379" shape="square" label="Equipment" />
                <LegendItem color="#e5c07b" shape="square" label="Pumps" />
                <LegendItem color="#c678dd" shape="square" label="Other" />
              </div>
            </div>
          )}
        </Panel>

        {/* Engineering Q&A Assistant */}
        <ChatPanel nodes={nodes} edges={edges} />
      </ReactFlow>
      
      {/* Maintenance Checklist Modal */}
      {showMaintenanceChecklist && selectedEquipment && (
        <MaintenanceChecklist
          equipmentType={selectedEquipment.type}
          equipmentTag={selectedEquipment.tag}
          equipmentDescription={selectedEquipment.description}
          onClose={() => setShowMaintenanceChecklist(false)}
        />
      )}
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
