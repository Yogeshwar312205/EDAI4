/**
 * Interactive Flow Simulator with Valve Control
 * 
 * Features:
 * - Click valves to toggle open/closed state
 * - Select source node to start simulation
 * - Animated flow visualization
 * - Real-time graph updates
 */

import React, { useState, useCallback } from 'react';
import { Workflow, Play, Square, Power, PowerOff, Zap, AlertCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';

interface FlowSimulationRequest {
  topology: {
    nodes: Array<{
      id: string;
      type: string;
      label?: string;
      x: number;
      y: number;
    }>;
    edges: Array<{
      source: string;
      target: string;
      type?: string;
    }>;
  };
  start_node_id: string;
  closed_valve_ids: string[];
}

interface FlowSimulationResponse {
  active_node_ids: string[];
  active_edge_ids: string[];
  blocked_nodes: string[];
  flow_path: string[];
  total_distance: number;
  message: string;
}

export const InteractiveFlowSimulator: React.FC = () => {
  const { graphData, setFlowSimulationResult } = useAppStore();
  const [closedValves, setClosedValves] = useState<Set<string>>(new Set());
  const [startNodeId, setStartNodeId] = useState<string>('');
  const [simulationResult, setSimulationResult] = useState<FlowSimulationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationError, setSimulationError] = useState<string | null>(null);

  // Get all valve nodes
  const valveNodes = graphData?.nodes.filter(node => 
    node.type?.toLowerCase().includes('valve')
  ) || [];

  // Get all nodes for source selection
  const allNodes = graphData?.nodes || [];

  // Mutation for flow simulation
  const simulateMutation = useMutation({
    mutationFn: async (request: FlowSimulationRequest) => {
      const response = await api.post<FlowSimulationResponse>(
        '/api/simulate-flow',  // Will become /api/simulate-flow after rewrite strips first /api
        request
      );
      return response.data;
    },
    onSuccess: (data) => {
      console.log('Simulation success:', data);
      setSimulationResult(data);
      setFlowSimulationResult(data); // Store in global state for GraphViewer
      setIsSimulating(false);
      setSimulationError(null);
    },
    onError: (error: any) => {
      console.error('Flow simulation error:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Simulation failed';
      setSimulationError(errorMessage);
      setIsSimulating(false);
    },
  });

  // Toggle valve state
  const toggleValve = useCallback((valveId: string) => {
    setClosedValves(prev => {
      const newSet = new Set(prev);
      if (newSet.has(valveId)) {
        newSet.delete(valveId);
      } else {
        newSet.add(valveId);
      }
      return newSet;
    });
  }, []);

  // Run simulation
  const runSimulation = useCallback(() => {
    if (!startNodeId || !graphData) {
      console.log('Cannot run simulation:', { startNodeId, hasGraphData: !!graphData });
      return;
    }

    console.log('Starting simulation...', { startNodeId, closedValves: Array.from(closedValves) });
    setIsSimulating(true);

    const request: FlowSimulationRequest = {
      topology: {
        nodes: graphData.nodes.map(node => ({
          id: node.id,
          type: node.type || 'unknown',
          label: node.label || node.tag || node.id,
          x: node.x || 0,
          y: node.y || 0,
        })),
        edges: graphData.edges.map(edge => ({
          source: edge.source,
          target: edge.target,
          type: edge.type || 'connected_to',
        })),
      },
      start_node_id: startNodeId,
      closed_valve_ids: Array.from(closedValves),
    };

    console.log('Simulation request:', request);
    simulateMutation.mutate(request);
  }, [startNodeId, graphData, closedValves, simulateMutation]);

  // NOTE: Auto-run disabled to prevent infinite loops
  // Users must click "Run Simulation" button manually

  // Reset simulation
  const resetSimulation = useCallback(() => {
    setClosedValves(new Set());
    setStartNodeId('');
    setSimulationResult(null);
    setFlowSimulationResult(null); // Clear global state
  }, [setFlowSimulationResult]);

  if (!graphData) {
    return (
      <div className="h-full bg-industrial-900 rounded-lg border border-industrial-600 flex items-center justify-center">
        <div className="text-center p-8">
          <AlertCircle className="w-16 h-16 text-industrial-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-industrial-200 mb-2">
            No Graph Data
          </h3>
          <p className="text-sm text-industrial-400">
            Upload and process a P&ID image to use the flow simulator.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-industrial-900 rounded-lg border border-industrial-600 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-industrial-600">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-accent-purple/20 rounded-lg flex items-center justify-center">
              <Workflow className="w-6 h-6 text-accent-purple" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-industrial-100">
                Interactive Flow Simulator
              </h2>
              <p className="text-sm text-industrial-400">
                Click valves to control flow, select source to simulate
              </p>
            </div>
          </div>
          <button
            onClick={resetSimulation}
            className="px-4 py-2 bg-industrial-700 hover:bg-industrial-600 text-industrial-200 rounded-lg transition-all"
          >
            Reset
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Total Valves"
            value={valveNodes.length}
            icon={<Power className="w-4 h-4" />}
            color="blue"
          />
          <StatCard
            label="Closed Valves"
            value={closedValves.size}
            icon={<PowerOff className="w-4 h-4" />}
            color="red"
          />
          <StatCard
            label="Active Nodes"
            value={simulationResult?.active_node_ids.length || 0}
            icon={<Zap className="w-4 h-4" />}
            color="green"
          />
          <StatCard
            label="Active Pipes"
            value={simulationResult?.active_edge_ids.length || 0}
            icon={<Workflow className="w-4 h-4" />}
            color="cyan"
          />
        </div>
      </div>

      {/* Controls */}
      <div className="p-6 border-b border-industrial-600 bg-industrial-800">
        <div className="space-y-4">
          {/* Source Node Selection */}
          <div>
            <label className="block text-sm font-medium text-industrial-300 mb-2">
              Flow Source Node
            </label>
            <select
              value={startNodeId}
              onChange={(e) => setStartNodeId(e.target.value)}
              className="w-full px-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue"
            >
              <option value="">Select source node...</option>
              {allNodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.label || node.tag || node.id} ({node.type})
                </option>
              ))}
            </select>
          </div>

          {/* Valve Controls */}
          <div>
            <label className="block text-sm font-medium text-industrial-300 mb-2">
              Valve Controls ({valveNodes.length} valves)
            </label>
            <div className="max-h-48 overflow-auto space-y-2 bg-industrial-900 rounded-lg p-3 border border-industrial-600">
              {valveNodes.length === 0 ? (
                <p className="text-sm text-industrial-500 text-center py-4">
                  No valves detected in topology
                </p>
              ) : (
                valveNodes.map((valve) => {
                  const isClosed = closedValves.has(valve.id);
                  return (
                    <button
                      key={valve.id}
                      onClick={() => toggleValve(valve.id)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg transition-all ${
                        isClosed
                          ? 'bg-accent-red/20 border-2 border-accent-red'
                          : 'bg-industrial-800 border-2 border-accent-green'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {isClosed ? (
                          <PowerOff className="w-5 h-5 text-accent-red" />
                        ) : (
                          <Power className="w-5 h-5 text-accent-green" />
                        )}
                        <div className="text-left">
                          <p className={`text-sm font-semibold ${
                            isClosed ? 'text-accent-red' : 'text-accent-green'
                          }`}>
                            {valve.label || valve.tag || valve.id}
                          </p>
                          <p className="text-xs text-industrial-400">
                            {valve.type}
                          </p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        isClosed
                          ? 'bg-accent-red text-white'
                          : 'bg-accent-green text-industrial-950'
                      }`}>
                        {isClosed ? 'CLOSED' : 'OPEN'}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Simulate Button */}
          <button
            onClick={runSimulation}
            disabled={!startNodeId || isSimulating}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-accent-blue hover:bg-accent-blue/80 disabled:bg-industrial-600 disabled:cursor-not-allowed text-industrial-950 font-semibold rounded-lg transition-all"
          >
            {isSimulating ? (
              <>
                <div className="w-5 h-5 border-2 border-industrial-950 border-t-transparent rounded-full animate-spin" />
                Simulating...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Run Simulation
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-6">
        {simulationError ? (
          <div className="bg-accent-red/10 border border-accent-red rounded-lg p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-accent-red" />
              <div>
                <p className="text-sm font-semibold text-accent-red mb-1">
                  Simulation Error
                </p>
                <p className="text-xs text-accent-red/80">
                  {simulationError}
                </p>
              </div>
            </div>
          </div>
        ) : simulationResult ? (
          <div className="space-y-4">
            {/* Message */}
            <div className={`p-4 rounded-lg border ${
              simulationResult.blocked_nodes.length > 0
                ? 'bg-accent-yellow/10 border-accent-yellow'
                : 'bg-accent-green/10 border-accent-green'
            }`}>
              <p className={`text-sm font-medium ${
                simulationResult.blocked_nodes.length > 0
                  ? 'text-accent-yellow'
                  : 'text-accent-green'
              }`}>
                {simulationResult.message}
              </p>
            </div>

            {/* Flow Path */}
            <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
              <h3 className="text-sm font-semibold text-industrial-300 mb-3">
                Flow Path ({simulationResult.flow_path.length} nodes)
              </h3>
              <div className="space-y-2 max-h-64 overflow-auto">
                {simulationResult.flow_path.map((nodeId, idx) => {
                  const node = allNodes.find(n => n.id === nodeId);
                  const isBlocked = simulationResult.blocked_nodes.includes(nodeId);
                  return (
                    <div
                      key={idx}
                      className={`flex items-center gap-2 p-2 rounded ${
                        isBlocked
                          ? 'bg-accent-red/20 border border-accent-red'
                          : 'bg-industrial-900'
                      }`}
                    >
                      <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${
                        isBlocked
                          ? 'bg-accent-red text-white'
                          : 'bg-accent-blue text-industrial-950'
                      }`}>
                        {idx + 1}
                      </span>
                      <span className="text-sm text-industrial-300 font-mono">
                        {node?.label || node?.tag || nodeId}
                      </span>
                      {isBlocked && (
                        <Square className="w-4 h-4 text-accent-red ml-auto" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
                <p className="text-xs text-industrial-500 mb-1">Total Distance</p>
                <p className="text-lg font-bold text-accent-blue">
                  {simulationResult.total_distance.toFixed(1)}px
                </p>
              </div>
              <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
                <p className="text-xs text-industrial-500 mb-1">Blocked Nodes</p>
                <p className="text-lg font-bold text-accent-red">
                  {simulationResult.blocked_nodes.length}
                </p>
              </div>
            </div>

            {/* Visualization Hint */}
            <div className="bg-accent-blue/10 border border-accent-blue rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="text-2xl">💡</div>
                <div>
                  <p className="text-sm font-semibold text-accent-blue mb-1">
                    View Animated Flow
                  </p>
                  <p className="text-xs text-accent-blue/80">
                    Switch to the <strong>Graph</strong> tab to see the flow animation with highlighted nodes and animated edges
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Workflow className="w-16 h-16 text-industrial-600 mx-auto mb-4" />
              <p className="text-industrial-400 mb-2">No simulation run yet</p>
              <p className="text-sm text-industrial-500">
                Select a source node and configure valves to start
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard: React.FC<{
  label: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'red' | 'green' | 'cyan';
}> = ({ label, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-accent-blue/20 text-accent-blue',
    red: 'bg-accent-red/20 text-accent-red',
    green: 'bg-accent-green/20 text-accent-green',
    cyan: 'bg-accent-cyan/20 text-accent-cyan',
  };

  return (
    <div className="bg-industrial-800 rounded-lg p-3 border border-industrial-600">
      <div className="flex items-center gap-2 mb-1">
        <div className={`p-1 rounded ${colorClasses[color]}`}>
          {icon}
        </div>
        <p className="text-xs text-industrial-500">{label}</p>
      </div>
      <p className="text-2xl font-bold text-industrial-100">{value}</p>
    </div>
  );
};

export default InteractiveFlowSimulator;
