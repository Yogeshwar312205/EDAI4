/**
 * HazOp Failure Simulator Component
 * 
 * Allows users to simulate equipment failures and visualize cascading effects
 * on the P&ID canvas using AI-powered HazOp analysis.
 */

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  Panel,
  NodeMouseHandler,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AlertTriangle, X, Zap, Shield, Activity, Info } from 'lucide-react';
import axios from 'axios';
import { CustomHazOpNode } from './CustomHazOpNode';
import { HazOpLegend } from './HazOpLegend';

// ============================================
// Types
// ============================================

interface HazOpSimulationRequest {
  failed_node_id: string;
  failure_mode: string;
  topology: {
    nodes: any[];
    edges: any[];
  };
}

interface HazOpSimulationResponse {
  hazard_summary: string;
  cascading_effects: string[];
  affected_node_ids: string[];
  affected_edge_ids: string[];
  severity_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommended_actions: string[];
}

interface ContextMenuProps {
  x: number;
  y: number;
  nodeId: string;
  onSimulate: (nodeId: string, failureMode: string) => void;
  onClose: () => void;
}

// ============================================
// Context Menu Component
// ============================================

const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, nodeId, onSimulate, onClose }) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const failureModes = [
    { label: 'Stuck Closed', icon: '🔒', color: 'text-red-400' },
    { label: 'Failed Open', icon: '🔓', color: 'text-orange-400' },
    { label: 'Leaking', icon: '💧', color: 'text-blue-400' },
    { label: 'Blocked', icon: '🚫', color: 'text-yellow-400' },
  ];

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-industrial-800 border-2 border-red-500 rounded-lg shadow-2xl shadow-red-500/20 min-w-[200px]"
      style={{ left: x, top: y }}
    >
      <div className="px-3 py-2 border-b border-industrial-600 bg-industrial-750">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-red-400" />
          <span className="text-xs font-bold text-industrial-100 uppercase tracking-wide">
            Simulate Failure
          </span>
        </div>
        <div className="text-xs text-industrial-400 mt-1 font-mono">{nodeId}</div>
      </div>

      <div className="py-1">
        {failureModes.map((mode) => (
          <button
            key={mode.label}
            onClick={() => {
              onSimulate(nodeId, mode.label);
              onClose();
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-industrial-700 transition-colors flex items-center gap-3 group"
          >
            <span className="text-lg">{mode.icon}</span>
            <span className={`${mode.color} group-hover:text-industrial-100 transition-colors`}>
              {mode.label}
            </span>
          </button>
        ))}
      </div>

      <div className="px-3 py-2 border-t border-industrial-600 bg-industrial-750">
        <button
          onClick={onClose}
          className="text-xs text-industrial-400 hover:text-industrial-200 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

// ============================================
// Analysis Panel Component
// ============================================

interface AnalysisPanelProps {
  result: HazOpSimulationResponse | null;
  failedNodeId: string;
  failureMode: string;
  onClear: () => void;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ result, failedNodeId, failureMode, onClear }) => {
  if (!result) return null;

  const severityColors = {
    LOW: 'text-green-400 border-green-500 bg-green-500/10',
    MEDIUM: 'text-yellow-400 border-yellow-500 bg-yellow-500/10',
    HIGH: 'text-orange-400 border-orange-500 bg-orange-500/10',
    CRITICAL: 'text-red-400 border-red-500 bg-red-500/10',
  };

  const severityColor = severityColors[result.severity_level] || severityColors.MEDIUM;

  return (
    <div className="fixed top-20 right-6 w-96 max-h-[calc(100vh-120px)] overflow-y-auto bg-industrial-900 border-2 border-red-500 rounded-lg shadow-2xl shadow-red-500/30 z-40 animate-slide-in">
      {/* Header */}
      <div className="sticky top-0 bg-gradient-to-r from-red-900 to-red-800 px-4 py-3 border-b border-red-600 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-200 animate-pulse" />
          <div>
            <h3 className="text-lg font-bold text-red-100">HazOp Analysis Report</h3>
            <p className="text-xs text-red-200 font-mono">{failedNodeId} - {failureMode}</p>
          </div>
        </div>
        <button
          onClick={onClear}
          className="p-1 hover:bg-red-700 rounded transition-colors"
        >
          <X className="w-5 h-5 text-red-200" />
        </button>
      </div>

      {/* Severity Badge */}
      <div className="px-4 py-3 border-b border-industrial-700">
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${severityColor} font-bold text-sm`}>
          <Shield className="w-4 h-4" />
          SEVERITY: {result.severity_level}
        </div>
      </div>

      {/* Hazard Summary */}
      <div className="px-4 py-4 border-b border-industrial-700">
        <h4 className="text-sm font-bold text-red-400 mb-2 uppercase tracking-wide flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          Immediate Hazard
        </h4>
        <p className="text-sm text-industrial-200 leading-relaxed">{result.hazard_summary}</p>
      </div>

      {/* Cascading Effects */}
      <div className="px-4 py-4 border-b border-industrial-700">
        <h4 className="text-sm font-bold text-orange-400 mb-3 uppercase tracking-wide flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Cascading Effects
        </h4>
        <ul className="space-y-2">
          {result.cascading_effects.map((effect, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-industrial-300">
              <span className="text-orange-400 mt-0.5">▸</span>
              <span>{effect}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Affected Equipment */}
      <div className="px-4 py-4 border-b border-industrial-700">
        <h4 className="text-sm font-bold text-yellow-400 mb-3 uppercase tracking-wide">
          Affected Equipment
        </h4>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-industrial-400 mb-1">Nodes in Danger Zone:</p>
            <div className="flex flex-wrap gap-1">
              {result.affected_node_ids.slice(0, 10).map((nodeId) => (
                <span
                  key={nodeId}
                  className="px-2 py-1 bg-red-500/20 border border-red-500/50 rounded text-xs text-red-300 font-mono"
                >
                  {nodeId}
                </span>
              ))}
              {result.affected_node_ids.length > 10 && (
                <span className="px-2 py-1 text-xs text-industrial-400">
                  +{result.affected_node_ids.length - 10} more
                </span>
              )}
            </div>
          </div>
          <div>
            <p className="text-xs text-industrial-400 mb-1">Affected Connections:</p>
            <div className="flex flex-wrap gap-1">
              {result.affected_edge_ids.slice(0, 10).map((edgeId) => (
                <span
                  key={edgeId}
                  className="px-2 py-1 bg-orange-500/20 border border-orange-500/50 rounded text-xs text-orange-300 font-mono"
                >
                  {edgeId}
                </span>
              ))}
              {result.affected_edge_ids.length > 10 && (
                <span className="px-2 py-1 text-xs text-industrial-400">
                  +{result.affected_edge_ids.length - 10} more
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="px-4 py-4">
        <h4 className="text-sm font-bold text-green-400 mb-3 uppercase tracking-wide flex items-center gap-2">
          <Shield className="w-4 h-4" />
          Emergency Response
        </h4>
        <ol className="space-y-2">
          {result.recommended_actions.map((action, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-industrial-300">
              <span className="text-green-400 font-bold min-w-[20px]">{idx + 1}.</span>
              <span>{action}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Clear Button */}
      <div className="sticky bottom-0 px-4 py-3 bg-industrial-800 border-t border-industrial-700">
        <button
          onClick={onClear}
          className="w-full px-4 py-2 bg-industrial-700 hover:bg-industrial-600 text-industrial-100 rounded-lg font-medium transition-colors"
        >
          Clear Simulation
        </button>
      </div>
    </div>
  );
};

// ============================================
// Main HazOp Simulator Component
// ============================================

interface HazOpSimulatorProps {
  initialNodes: Node[];
  initialEdges: Edge[];
}

export const HazOpSimulator: React.FC<HazOpSimulatorProps> = ({ initialNodes, initialEdges }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null);
  const [simulationResult, setSimulationResult] = useState<HazOpSimulationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [failedNodeId, setFailedNodeId] = useState<string>('');
  const [failureMode, setFailureMode] = useState<string>('');

  // Define custom node types
  const nodeTypes = useMemo(() => ({
    custom: CustomHazOpNode,
  }), []);

  // Handle right-click on node
  const onNodeContextMenu: NodeMouseHandler = useCallback(
    (event, node) => {
      event.preventDefault();
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        nodeId: node.id,
      });
    },
    []
  );

  // Close context menu
  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  // Simulate failure
  const simulateFailure = useCallback(
    async (nodeId: string, failureMode: string) => {
      setIsSimulating(true);
      setFailedNodeId(nodeId);
      setFailureMode(failureMode);

      try {
        // Prepare topology data
        const topology = {
          nodes: nodes.map((n) => ({
            id: n.id,
            type: n.type || 'default',
            data: n.data,
            position: n.position,
          })),
          edges: edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            data: e.data || {},
          })),
        };

        // Call API
        const response = await axios.post<HazOpSimulationResponse>(
          'http://localhost:8000/api/simulate-hazop',
          {
            failed_node_id: nodeId,
            failure_mode: failureMode,
            topology,
          } as HazOpSimulationRequest
        );

        const result = response.data;
        setSimulationResult(result);

        // Apply visual effects
        applyVisualEffects(result);
      } catch (error: any) {
        console.error('HazOp simulation failed:', error);
        
        // Better error messages
        let errorMessage = 'Failed to run HazOp simulation.';
        
        if (error.response?.status === 503) {
          errorMessage = '⚠️ Backend service unavailable.\n\n' +
            'Possible causes:\n' +
            '1. Backend server is not running (start with: python -m uvicorn src.api.main:app --reload --port 8000)\n' +
            '2. Gemini API quota exceeded (free tier: 15 req/min)\n' +
            '3. Gemini API key is invalid\n\n' +
            'Check backend terminal for error details.';
        } else if (error.response?.status === 500) {
          errorMessage = '⚠️ Backend error occurred.\n\n' +
            'Check backend terminal for error details.';
        } else if (error.code === 'ERR_NETWORK') {
          errorMessage = '⚠️ Cannot connect to backend.\n\n' +
            'Make sure backend is running on http://localhost:8000\n' +
            'Start with: python -m uvicorn src.api.main:app --reload --port 8000';
        }
        
        alert(errorMessage);
      } finally {
        setIsSimulating(false);
      }
    },
    [nodes, edges]
  );

  // Apply visual effects to affected nodes and edges
  const applyVisualEffects = useCallback(
    (result: HazOpSimulationResponse) => {
      // Update nodes
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === failedNodeId) {
            // Failed node - red pulsing
            return {
              ...node,
              style: {
                ...node.style,
                border: '3px solid #ef4444',
                boxShadow: '0 0 20px #ef4444, 0 0 40px #ef4444',
                animation: 'pulse 1.5s ease-in-out infinite',
              },
            };
          } else if (result.affected_node_ids.includes(node.id)) {
            // Affected nodes - orange glow
            return {
              ...node,
              style: {
                ...node.style,
                border: '2px solid #f97316',
                boxShadow: '0 0 15px #f97316',
              },
            };
          }
          return node;
        })
      );

      // Update edges
      setEdges((eds) =>
        eds.map((edge) => {
          if (result.affected_edge_ids.includes(edge.id)) {
            // Affected edges - animated red glow
            return {
              ...edge,
              animated: true,
              style: {
                ...edge.style,
                stroke: '#ef4444',
                strokeWidth: 3,
                filter: 'drop-shadow(0 0 8px #ef4444)',
              },
            };
          }
          return edge;
        })
      );
    },
    [failedNodeId, setNodes, setEdges]
  );

  // Clear simulation
  const clearSimulation = useCallback(() => {
    setSimulationResult(null);
    setFailedNodeId('');
    setFailureMode('');

    // Reset node styles
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        style: {
          ...node.style,
          border: undefined,
          boxShadow: undefined,
          animation: undefined,
        },
      }))
    );

    // Reset edge styles
    setEdges((eds) =>
      eds.map((edge) => ({
        ...edge,
        animated: false,
        style: {
          ...edge.style,
          stroke: undefined,
          strokeWidth: undefined,
          filter: undefined,
        },
      }))
    );
  }, [setNodes, setEdges]);

  return (
    <div className="w-full h-full relative bg-industrial-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeContextMenu={onNodeContextMenu}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          animated: false,
          style: { stroke: '#61afef', strokeWidth: 2 }
        }}
      >
        <Background 
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#3d4556"
        />
        
        <Controls 
          className="!bg-industrial-800 !border-industrial-600"
          showInteractive={false}
        />
        
        <MiniMap
          nodeColor={(node) => {
            if (node.id === failedNodeId) return '#ef4444';
            if (simulationResult?.affected_node_ids.includes(node.id)) return '#f97316';
            return '#61afef';
          }}
          nodeStrokeWidth={3}
          nodeBorderRadius={8}
          className="!bg-industrial-800 !border-2 !border-industrial-600 !rounded-lg"
          maskColor="rgba(10, 14, 20, 0.8)"
        />

        {/* Info Panel */}
        <Panel position="top-left" className="bg-industrial-800 border border-industrial-600 rounded-lg p-3 shadow-lg">
          <div className="flex items-center gap-2 text-sm">
            <Info className="w-4 h-4 text-accent-blue" />
            <div>
              <div className="text-industrial-100 font-semibold">HazOp Simulator</div>
              <div className="text-industrial-400 text-xs">Right-click nodes to simulate failures</div>
            </div>
          </div>
          <div className="mt-2 pt-2 border-t border-industrial-600 text-xs text-industrial-400">
            <div>Nodes: {nodes.length}</div>
            <div>Edges: {edges.length}</div>
          </div>
        </Panel>

        {/* Loading Overlay */}
        {isSimulating && (
          <Panel position="top-center">
            <div className="bg-industrial-900 border-2 border-accent-blue px-6 py-3 rounded-lg shadow-glow-blue flex items-center gap-3">
              <div className="animate-spin">
                <Zap className="w-5 h-5 text-accent-blue" />
              </div>
              <span className="text-industrial-100 font-medium">Running HazOp Simulation...</span>
            </div>
          </Panel>
        )}
      </ReactFlow>

      {/* Context Menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          nodeId={contextMenu.nodeId}
          onSimulate={simulateFailure}
          onClose={closeContextMenu}
        />
      )}

      {/* Analysis Panel */}
      <AnalysisPanel
        result={simulationResult}
        failedNodeId={failedNodeId}
        failureMode={failureMode}
        onClear={clearSimulation}
      />

      {/* Legend */}
      <HazOpLegend />
    </div>
  );
};

export default HazOpSimulator;
