// Feature 3: Topology/Knowledge Graph Viewer with Physics
import React, { useCallback, useMemo, useState } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useAppStore } from '@/store/useAppStore';
import type { GraphData } from '@/types/api';
import { AlertCircle } from 'lucide-react';

interface GraphViewerProps {
  graphData: GraphData;
}

export const GraphViewer: React.FC<GraphViewerProps> = ({ graphData }) => {
  const { selectedNodeId, setSelectedNodeId } = useAppStore();
  const [error, setError] = useState<string | null>(null);

  // Transform backend graph data to ReactFlow format with error handling
  const { initialNodes, initialEdges } = useMemo(() => {
    try {
      // Validate graph data
      if (!graphData || !graphData.nodes || !Array.isArray(graphData.nodes)) {
        throw new Error('Invalid graph data: nodes array is missing');
      }

      if (!graphData.edges || !Array.isArray(graphData.edges)) {
        console.warn('No edges found in graph data');
      }

      const nodes: Node[] = graphData.nodes
        .filter((node) => {
          // Filter out invalid nodes
          if (!node.id) {
            console.warn('Skipping node without id:', node);
            return false;
          }
          if (typeof node.x !== 'number' || typeof node.y !== 'number') {
            console.warn('Skipping node with invalid coordinates:', node);
            return false;
          }
          return true;
        })
        .map((node) => {
          const nodeType = getNodeType(node.type);
          const color = getNodeColor(node.type);
          
          return {
            id: node.id,
            type: nodeType.shape,
            position: { 
              x: Math.max(0, node.x * 2), // Scale up and ensure positive
              y: Math.max(0, node.y * 2) 
            },
            data: {
              label: node.tag || node.label || node.id,
              type: node.type,
            },
            style: {
              background: color,
              color: '#0a0e14',
              border: `2px solid ${color}`,
              borderRadius: nodeType.shape === 'default' ? '50%' : '8px',
              padding: 10,
              fontSize: 12,
              fontWeight: 'bold',
              fontFamily: 'monospace',
              width: nodeType.shape === 'default' ? 80 : 120,
              height: nodeType.shape === 'default' ? 80 : 60,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 0 20px ${color}40`,
            },
          };
        });

      const edges: Edge[] = (graphData.edges || [])
        .filter((edge) => {
          // Filter out invalid edges
          if (!edge.source || !edge.target) {
            console.warn('Skipping edge without source/target:', edge);
            return false;
          }
          // Check if source and target nodes exist
          const sourceExists = nodes.some(n => n.id === edge.source);
          const targetExists = nodes.some(n => n.id === edge.target);
          if (!sourceExists || !targetExists) {
            console.warn('Skipping edge with missing nodes:', edge);
            return false;
          }
          return true;
        })
        .map((edge, index) => ({
          id: `edge-${index}`,
          source: edge.source,
          target: edge.target,
          type: ConnectionLineType.Bezier,
          animated: edge.type === 'flow',
          style: {
            stroke: getEdgeColor(edge.type),
            strokeWidth: 2,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: getEdgeColor(edge.type),
          },
          label: edge.type,
          labelStyle: {
            fill: '#abb2bf',
            fontSize: 10,
            fontFamily: 'monospace',
          },
          labelBgStyle: {
            fill: '#1a1f29',
            fillOpacity: 0.8,
          },
        }));

      // Check if we have valid data
      if (nodes.length === 0) {
        throw new Error('No valid nodes found in graph data');
      }

      setError(null);
      return { initialNodes: nodes, initialEdges: edges };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('Error processing graph data:', err);
      setError(errorMessage);
      return { initialNodes: [], initialEdges: [] };
    }
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Handle node click
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
    },
    [setSelectedNodeId]
  );

  // Highlight selected node
  React.useEffect(() => {
    if (nodes.length === 0) return;
    
    setNodes((nds) =>
      nds.map((node) => {
        const borderColor = node.style?.border?.split(' ')[2] || '#61afef';
        return {
          ...node,
          style: {
            ...node.style,
            boxShadow:
              selectedNodeId === node.id
                ? `0 0 30px ${borderColor}`
                : `0 0 20px ${borderColor}40`,
            transform: selectedNodeId === node.id ? 'scale(1.1)' : 'scale(1)',
            transition: 'all 0.3s ease',
          },
        };
      })
    );
  }, [selectedNodeId, setNodes, nodes.length]);

  // Show error state
  if (error) {
    return (
      <div className="w-full h-full bg-industrial-900 rounded-lg overflow-hidden border border-industrial-600 flex items-center justify-center">
        <div className="text-center p-8">
          <AlertCircle className="w-16 h-16 text-accent-red mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-industrial-200 mb-2">
            Graph Visualization Error
          </h3>
          <p className="text-sm text-industrial-400 mb-4">{error}</p>
          <p className="text-xs text-industrial-500">
            Please process a P&ID image first to generate graph data.
          </p>
        </div>
      </div>
    );
  }

  // Show empty state
  if (initialNodes.length === 0) {
    return (
      <div className="w-full h-full bg-industrial-900 rounded-lg overflow-hidden border border-industrial-600 flex items-center justify-center">
        <div className="text-center p-8">
          <AlertCircle className="w-16 h-16 text-industrial-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-industrial-200 mb-2">
            No Graph Data Available
          </h3>
          <p className="text-sm text-industrial-400">
            Upload and process a P&ID image to view the topology graph.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-industrial-900 rounded-lg overflow-hidden border border-industrial-600">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-left"
        className="bg-industrial-950"
      >
        <Background color="#3d4556" gap={16} />
        <Controls
          className="bg-industrial-800 border border-industrial-600 rounded-lg"
          style={{
            button: {
              backgroundColor: '#1a1f29',
              color: '#abb2bf',
              borderBottom: '1px solid #3d4556',
            },
          }}
        />
        <MiniMap
          nodeColor={(node) => {
            const borderColor = node.style?.border?.split(' ')[2];
            return borderColor || '#61afef';
          }}
          className="bg-industrial-800 border border-industrial-600 rounded-lg"
          maskColor="rgba(10, 14, 20, 0.8)"
        />
      </ReactFlow>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-industrial-800/95 backdrop-blur-sm rounded-lg p-4 border border-industrial-600 max-w-xs">
        <h3 className="text-sm font-bold text-industrial-200 mb-3 font-mono">
          Graph Legend
        </h3>
        <div className="space-y-2 text-xs">
          <LegendItem color="#61afef" shape="circle" label="Instruments" />
          <LegendItem color="#56b6c2" shape="circle" label="Valves" />
          <LegendItem color="#98c379" shape="square" label="Equipment" />
          <LegendItem color="#e5c07b" shape="square" label="Pumps" />
          <LegendItem color="#c678dd" shape="square" label="Other" />
        </div>
        <div className="mt-4 pt-3 border-t border-industrial-600 space-y-1 text-xs text-industrial-400">
          <div>🖱️ Drag nodes to rearrange</div>
          <div>🔍 Scroll to zoom</div>
          <div>📍 Click node to select</div>
        </div>
      </div>
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
      className={`w-4 h-4 border-2 ${
        shape === 'circle' ? 'rounded-full' : 'rounded'
      }`}
      style={{ borderColor: color, backgroundColor: `${color}40` }}
    />
    <span className="text-industrial-300 font-mono">{label}</span>
  </div>
);

// Helper Functions
const getNodeType = (
  type: string
): { shape: 'default' | 'input' | 'output' } => {
  if (type.includes('instrument') || type.includes('valve')) {
    return { shape: 'default' }; // Circle
  }
  return { shape: 'input' }; // Rectangle
};

const getNodeColor = (type: string): string => {
  if (type.includes('instrument')) return '#61afef';
  if (type.includes('valve')) return '#56b6c2';
  if (type.includes('equipment')) return '#98c379';
  if (type.includes('pump')) return '#e5c07b';
  return '#c678dd';
};

const getEdgeColor = (type: string): string => {
  if (type === 'flow') return '#98c379';
  if (type === 'signal') return '#61afef';
  if (type === 'control') return '#e5c07b';
  return '#828997';
};
