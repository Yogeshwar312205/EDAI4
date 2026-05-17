/**
 * Editable Graph Viewer - Interactive P&ID Editor
 * 
 * Allows users to:
 * - Drag and drop components from palette
 * - Connect nodes with edges
 * - Delete nodes and edges
 * - Save topology to JSON
 */

import React, { useCallback, useState, useRef, useEffect, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Controls,
  Background,
  MiniMap,
  Panel,
  BackgroundVariant,
  NodeMouseHandler,
  OnConnect,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  Save, 
  Edit3, 
  Eye, 
  Trash2, 
  Download,
  Upload,
  AlertCircle,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { ComponentPalette } from './ComponentPalette';
import { TextToTopologyPanel } from './TextToTopologyPanel';
import { useAppStore } from '@/store/useAppStore';
import axios from 'axios';
import { EnhancedNode } from './nodes/EnhancedNode';
import { generateDefaultTag, getNodeColor } from '@/utils/nodeUtils';

interface EditableGraphViewerProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onSave?: (nodes: Node[], edges: Edge[]) => void;
}

export const EditableGraphViewer: React.FC<EditableGraphViewerProps> = ({
  initialNodes,
  initialEdges,
  onSave,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [isEditMode, setIsEditMode] = useState(false);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [showTextToTopology, setShowTextToTopology] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  
  // Get store actions
  const { setGraphData, setActiveView } = useAppStore();

  // Counter for generating unique IDs
  const nodeIdCounter = useRef(1000);

  // Define custom node types
  const nodeTypes = useMemo(
    () => ({
      enhanced: EnhancedNode,
    }),
    []
  );

  // Update nodes when initialNodes change
  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  // Update edges when initialEdges change
  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Handle connection between nodes
  const onConnect: OnConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        ...params,
        id: `edge-${Date.now()}`,
        type: 'smoothstep',
        animated: true,
        style: {
          stroke: '#61afef',
          strokeWidth: 2,
        },
        markerEnd: {
          type: 'arrowclosed' as any,
          color: '#61afef',
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  // Handle drag over (required for drop to work)
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop of component from palette
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');
      const label = event.dataTransfer.getData('componentLabel');

      if (!type) return;

      // Calculate position on canvas
      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      // Generate unique ID
      const newNodeId = `${type}-${nodeIdCounter.current++}`;

      // Determine node color based on type
      const color = getNodeColor(type);

      // Generate default ISA tag
      const defaultTag = generateDefaultTag(type, nodeIdCounter.current - 1000);

      // Create new node with enhanced type
      const newNode: Node = {
        id: newNodeId,
        type: 'enhanced', // Use our custom enhanced node
        position,
        data: {
          label: `${label}`,
          type: type,
          tag: defaultTag,
        },
        style: {
          width: 140,
          height: 80,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  // Handle node click
  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNodes([node.id]);
    console.log('Selected node:', node);
  }, []);
  
  // Get selected node details
  const selectedNode = selectedNodes.length === 1 
    ? nodes.find(n => n.id === selectedNodes[0]) 
    : null;

  // Handle edge selection
  const onEdgeClick = useCallback((_, edge: Edge) => {
    setSelectedEdges([edge.id]);
  }, []);

  // Handle keyboard delete
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isEditMode) return;
      
      if (event.key === 'Delete' || event.key === 'Backspace') {
        // Delete selected nodes
        if (selectedNodes.length > 0) {
          setNodes((nds) => nds.filter((node) => !selectedNodes.includes(node.id)));
          setEdges((eds) => 
            eds.filter(
              (edge) => 
                !selectedNodes.includes(edge.source) && 
                !selectedNodes.includes(edge.target)
            )
          );
          setSelectedNodes([]);
        }
        
        // Delete selected edges
        if (selectedEdges.length > 0) {
          setEdges((eds) => eds.filter((edge) => !selectedEdges.includes(edge.id)));
          setSelectedEdges([]);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isEditMode, selectedNodes, selectedEdges, setNodes, setEdges]);

  // Save topology to JSON file
  const handleSaveToFile = useCallback(() => {
    const topology = {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        animated: edge.animated,
      })),
      metadata: {
        savedAt: new Date().toISOString(),
        nodeCount: nodes.length,
        edgeCount: edges.length,
      },
    };

    const blob = new Blob([JSON.stringify(topology, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pid-topology-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    // Call onSave callback if provided
    if (onSave) {
      onSave(nodes, edges);
    }
  }, [nodes, edges, onSave]);

  // Save topology to backend
  const handleSaveToBackend = useCallback(async () => {
    try {
      const topology = {
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: node.data,
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type,
        })),
      };

      await axios.post('/api/save-topology', topology);
      alert('Topology saved successfully!');
    } catch (error) {
      console.error('Failed to save topology:', error);
      alert('Failed to save topology to backend. Saving to file instead...');
      handleSaveToFile();
    }
  }, [nodes, edges, handleSaveToFile]);

  // Handle topology generated from AI
  const handleTopologyGenerated = useCallback((generatedNodes: any[], generatedEdges: any[]) => {
    console.log('Adding generated topology:', { nodes: generatedNodes.length, edges: generatedEdges.length });
    
    // Convert generated nodes to React Flow format
    const newNodes: Node[] = generatedNodes.map((node) => ({
      id: node.id,
      type: 'enhanced',
      position: { x: node.x, y: node.y },
      data: {
        label: node.label,
        tag: node.tag,
        type: node.type,
        description: node.description,
      },
      style: {
        background: `linear-gradient(135deg, ${getNodeColor(node.type)} 0%, ${getNodeColor(node.type)}dd 100%)`,
        color: '#ffffff',
        border: `2px solid ${getNodeColor(node.type)}`,
        borderRadius: '8px',
        padding: '12px',
        fontSize: '13px',
        fontWeight: 600,
        minWidth: 140,
        minHeight: 70,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: `0 4px 6px ${getNodeColor(node.type)}40`,
        textAlign: 'center',
      },
    }));
    
    // Convert generated edges to React Flow format
    const newEdges: Edge[] = generatedEdges.map((edge, index) => ({
      id: `generated-edge-${Date.now()}-${index}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: false,
      style: {
        stroke: '#61afef',
        strokeWidth: 2,
      },
      markerEnd: {
        type: 'arrowclosed' as any,
        color: '#61afef',
      },
      label: edge.label,
    }));
    
    // Add to existing nodes and edges
    setNodes((nds) => [...nds, ...newNodes]);
    setEdges((eds) => [...eds, ...newEdges]);
    
    // Close the panel
    setShowTextToTopology(false);
    
    // Show success message
    console.log(`✅ Added ${newNodes.length} nodes and ${newEdges.length} edges to canvas`);
  }, [setNodes, setEdges]);

  // Load topology from file
  const handleLoadFromFile = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e: any) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const topology = JSON.parse(event.target?.result as string);
          setNodes(topology.nodes || []);
          setEdges(topology.edges || []);
          alert('Topology loaded successfully!');
        } catch (error) {
          console.error('Failed to load topology:', error);
          alert('Failed to load topology file.');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  }, [setNodes, setEdges]);

  // Clear all nodes and edges
  const handleClear = useCallback(() => {
    if (confirm('Are you sure you want to clear the entire diagram?')) {
      setNodes([]);
      setEdges([]);
    }
  }, [setNodes, setEdges]);

  // Update Graph and HazOp views with current topology
  const handleUpdateGraphAndHazOp = useCallback(() => {
    try {
      // Convert React Flow nodes back to backend GraphData format
      const backendNodes = nodes.map(node => ({
        id: node.id,
        type: node.data?.type || node.type || 'equipment',
        tag: node.data?.tag || node.data?.label || node.id,
        label: node.data?.label || node.id,
        x: node.position.x,
        y: node.position.y,
      }));
      
      // Convert React Flow edges back to backend GraphData format
      const backendEdges = edges.map(edge => ({
        source: edge.source,
        target: edge.target,
        type: edge.type || 'connected_to',
      }));
      
      // Create the graph data in backend format
      const updatedGraphData = {
        nodes: backendNodes,
        edges: backendEdges,
      };
      
      console.log('=== UPDATING GRAPH DATA ===');
      console.log('Nodes:', updatedGraphData.nodes.length);
      console.log('Edges:', updatedGraphData.edges.length);
      console.log('Sample backend node:', updatedGraphData.nodes[0]);
      console.log('Backend format check:');
      console.log('  - Has x/y at root?', 'x' in updatedGraphData.nodes[0], 'y' in updatedGraphData.nodes[0]);
      console.log('  - Has position object?', 'position' in updatedGraphData.nodes[0]);
      console.log('  - Has type?', 'type' in updatedGraphData.nodes[0]);
      console.log('  - Has label?', 'label' in updatedGraphData.nodes[0]);
      
      // Update the global graph data
      setGraphData(updatedGraphData);
      
      console.log('Graph data updated in store');
      console.log('You can now switch to Graph tab to see the changes');
      
      // Show success message
      alert('✅ Graph and HazOp views updated successfully!\n\nYou can now switch to the Graph or HazOp tab to see your changes.');
      
      // Optionally switch to Graph view
      // setActiveView('graph');
    } catch (error) {
      console.error('Failed to update graph:', error);
      alert('❌ Failed to update Graph and HazOp views.');
    }
  }, [nodes, edges, setGraphData]);

  return (
    <div className="w-full h-full relative" ref={reactFlowWrapper}>
      {/* Component Palette */}
      <ComponentPalette isEditMode={isEditMode} />

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        nodesDraggable={isEditMode}
        nodesConnectable={isEditMode}
        elementsSelectable={isEditMode}
        fitView
        minZoom={0.1}
        maxZoom={2}
        className="bg-industrial-950"
      >
        <Background 
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#3d4556"
        />
        
        <Controls
          className="!bg-industrial-800/90 !border-industrial-600 !rounded-xl !shadow-2xl"
          position="bottom-left"
          showInteractive={false}
        />
        
        <MiniMap
          nodeColor={(node) => {
            const border = node.style?.border;
            const borderColor = typeof border === 'string' ? border.split(' ')[2] : '#61afef';
            return borderColor || '#61afef';
          }}
          nodeStrokeWidth={3}
          className="!bg-industrial-800/90 !border-industrial-600 !rounded-xl !shadow-2xl"
          maskColor="rgba(10, 14, 20, 0.6)"
          position="bottom-right"
        />

        {/* Top Toolbar */}
        <Panel position="top-center" className="flex items-center gap-3">
          {/* Edit Mode Toggle */}
          <button
            onClick={() => setIsEditMode(!isEditMode)}
            className={`
              px-4 py-2 rounded-full font-semibold text-sm
              flex items-center gap-2 shadow-2xl transition-all
              ${isEditMode
                ? 'bg-gradient-to-r from-accent-green to-accent-cyan text-white'
                : 'bg-industrial-800/95 backdrop-blur-md border border-industrial-600 text-industrial-200 hover:border-accent-blue'
              }
            `}
          >
            {isEditMode ? (
              <>
                <Edit3 className="w-4 h-4" />
                <span>Edit Mode</span>
              </>
            ) : (
              <>
                <Eye className="w-4 h-4" />
                <span>View Mode</span>
              </>
            )}
          </button>

          {/* Action Buttons (only in edit mode) */}
          {isEditMode && (
            <>
              {/* Update Graph & HazOp Button */}
              <button
                onClick={handleUpdateGraphAndHazOp}
                className="px-4 py-2 bg-gradient-to-r from-accent-green to-accent-cyan text-white font-semibold rounded-full shadow-2xl hover:scale-105 transition-all flex items-center gap-2 animate-pulse"
                title="Update Graph and HazOp views with current topology"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Update Graph & HazOp</span>
              </button>

              {/* Save Button */}
              <button
                onClick={handleSaveToFile}
                className="px-4 py-2 bg-gradient-to-r from-accent-blue to-accent-cyan text-white font-semibold rounded-full shadow-2xl hover:scale-105 transition-all flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                <span>Save Topology</span>
              </button>

              {/* AI Text-to-Topology Button */}
              <button
                onClick={() => setShowTextToTopology(!showTextToTopology)}
                className={`px-4 py-2 font-semibold rounded-full shadow-2xl hover:scale-105 transition-all flex items-center gap-2 ${
                  showTextToTopology
                    ? 'bg-gradient-to-r from-accent-purple to-accent-blue text-white'
                    : 'bg-gradient-to-r from-accent-purple/20 to-accent-blue/20 text-accent-purple border-2 border-accent-purple hover:from-accent-purple hover:to-accent-blue hover:text-white'
                }`}
                title="Generate topology from natural language using AI"
              >
                <Sparkles className="w-4 h-4" />
                <span>AI Draft</span>
              </button>

              {/* Load Button */}
              <button
                onClick={handleLoadFromFile}
                className="px-4 py-2 bg-industrial-800/95 backdrop-blur-md border border-industrial-600 text-industrial-200 font-semibold rounded-full shadow-2xl hover:border-accent-blue transition-all flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                <span>Load</span>
              </button>

              {/* Clear Button */}
              <button
                onClick={handleClear}
                className="px-4 py-2 bg-industrial-800/95 backdrop-blur-md border border-red-500/50 text-red-400 font-semibold rounded-full shadow-2xl hover:bg-red-500/10 transition-all flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Clear</span>
              </button>
            </>
          )}
        </Panel>

        {/* Stats Badge */}
        <Panel position="top-right" className="mr-4">
          <div className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-full px-4 py-2 shadow-2xl flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-accent-blue" />
              <span className="text-xs text-industrial-300">Nodes:</span>
              <span className="text-sm font-bold text-accent-blue font-mono">{nodes.length}</span>
            </div>
            <div className="w-px h-4 bg-industrial-600" />
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-accent-cyan" />
              <span className="text-xs text-industrial-300">Edges:</span>
              <span className="text-sm font-bold text-accent-cyan font-mono">{edges.length}</span>
            </div>
          </div>
        </Panel>

        {/* Node Info Panel (when node is selected) */}
        {selectedNode && (
          <Panel position="top-left" className="ml-4 mt-4">
            <div className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-xl p-4 shadow-2xl min-w-[280px]">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-industrial-100 flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ 
                      backgroundColor: getNodeColor(selectedNode.data?.type || 'other')
                    }}
                  />
                  Node Details
                </h3>
                <button
                  onClick={() => setSelectedNodes([])}
                  className="text-industrial-400 hover:text-industrial-200 transition-colors"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-2.5 text-xs">
                {/* Tag */}
                <div>
                  <span className="text-industrial-400">ISA Tag:</span>
                  <div className="text-accent-cyan font-bold font-mono mt-1 bg-industrial-900/50 px-3 py-2 rounded text-sm">
                    {selectedNode.data?.tag || 'UNTAGGED'}
                  </div>
                </div>
                
                {/* Label */}
                <div>
                  <span className="text-industrial-400">Label:</span>
                  <div className="text-industrial-100 font-semibold mt-1 bg-industrial-900/50 px-3 py-2 rounded">
                    {selectedNode.data?.label || 'N/A'}
                  </div>
                </div>
                
                {/* Type */}
                <div>
                  <span className="text-industrial-400">Type:</span>
                  <div className="text-industrial-100 font-medium mt-1 bg-industrial-900/50 px-3 py-2 rounded capitalize">
                    {selectedNode.data?.type || 'Unknown'}
                  </div>
                </div>
                
                {/* ID */}
                <div>
                  <span className="text-industrial-400">ID:</span>
                  <div className="text-industrial-300 font-mono text-[10px] mt-1 bg-industrial-900/50 px-3 py-2 rounded truncate">
                    {selectedNode.id}
                  </div>
                </div>
                
                {/* Position */}
                <div>
                  <span className="text-industrial-400">Position:</span>
                  <div className="text-industrial-300 font-mono text-[10px] mt-1 bg-industrial-900/50 px-3 py-2 rounded">
                    x: {selectedNode.position.x.toFixed(0)}, y: {selectedNode.position.y.toFixed(0)}
                  </div>
                </div>
              </div>

              {/* Edit Tag Button */}
              <div className="mt-4 pt-3 border-t border-industrial-700">
                <button
                  className="w-full px-3 py-2 bg-accent-blue/20 hover:bg-accent-blue/30 text-accent-blue font-semibold rounded-lg transition-colors text-xs"
                  onClick={() => {
                    const newTag = prompt('Enter new ISA tag:', selectedNode.data?.tag || '');
                    if (newTag) {
                      setNodes((nds) =>
                        nds.map((node) =>
                          node.id === selectedNode.id
                            ? { ...node, data: { ...node.data, tag: newTag.toUpperCase() } }
                            : node
                        )
                      );
                    }
                  }}
                >
                  Edit ISA Tag
                </button>
              </div>
            </div>
          </Panel>
        )}

        {/* Instructions (only in edit mode) */}
        {isEditMode && (
          <Panel position="bottom-center" className="mb-4">
            <div className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-xl px-4 py-2 shadow-2xl">
              <div className="flex items-center gap-6 text-xs text-industrial-400">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-accent-blue" />
                  <span>Drag components from left palette</span>
                </div>
                <div className="w-px h-4 bg-industrial-600" />
                <span>Connect nodes by dragging handles</span>
                <div className="w-px h-4 bg-industrial-600" />
                <span>Delete: Select + Backspace</span>
                <div className="w-px h-4 bg-industrial-600" />
                <span className="text-accent-green font-semibold">Click "Update Graph & HazOp" to sync changes</span>
              </div>
            </div>
          </Panel>
        )}
      </ReactFlow>
      
      {/* Text-to-Topology Panel (Floating) */}
      {showTextToTopology && (
        <div className="absolute top-4 right-4 w-96 h-[calc(100%-2rem)] z-50 animate-slide-in">
          <TextToTopologyPanel
            onTopologyGenerated={handleTopologyGenerated}
            existingNodes={nodes}
            existingEdges={edges}
            startPosition={{ x: 100, y: 100 }}
          />
        </div>
      )}
    </div>
  );
};

export default EditableGraphViewer;
