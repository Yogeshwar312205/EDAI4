// Flow Simulator - Digital Twin Topology Simulation
import React, { useState } from 'react';
import { Workflow, Play, Square, ArrowRight, Zap } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useAppStore } from '@/store/useAppStore';

interface FlowPath {
  start_node: string;
  end_node: string;
  path_nodes: string[];
  path_edges: string[];
  total_distance: number;
  blocked_by?: string;
}

interface SimulationResult {
  valve_id: string;
  action: 'open' | 'close';
  affected_nodes: string[];
  flow_status: string;
  message: string;
}

export const FlowSimulator: React.FC = () => {
  const [mode, setMode] = useState<'trace' | 'simulate'>('trace');
  const [startNode, setStartNode] = useState('');
  const [direction, setDirection] = useState<'downstream' | 'upstream'>('downstream');
  const [flowPath, setFlowPath] = useState<FlowPath | null>(null);
  
  // Valve simulation state
  const [selectedValve, setSelectedValve] = useState('');
  const [valveAction, setValveAction] = useState<'open' | 'close'>('close');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  
  const { processingResult } = useAppStore();

  const traceMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append('start_node', startNode);
      formData.append('direction', direction);

      const response = await axios.post('/api/flow/trace', formData);
      return response.data;
    },
    onSuccess: (data) => {
      setFlowPath(data);
    },
  });

  const simulateMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append('valve_id', selectedValve);
      formData.append('action', valveAction);

      const response = await axios.post('/api/flow/simulate', formData);
      return response.data;
    },
    onSuccess: (data) => {
      setSimulationResult(data);
    },
  });

  const handleTrace = () => {
    if (startNode) {
      traceMutation.mutate();
    }
  };

  const handleSimulate = () => {
    if (selectedValve) {
      simulateMutation.mutate();
    }
  };

  // Get valve nodes from detections
  const valveNodes = processingResult?.detections.filter(
    (det) => det.class_name.toLowerCase().includes('valve')
  ) || [];

  return (
    <div className="h-full bg-industrial-900 rounded-lg border border-industrial-600 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-industrial-600">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-accent-purple/20 rounded-lg flex items-center justify-center">
            <Workflow className="w-6 h-6 text-accent-purple" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-industrial-100">
              Flow Path Simulator
            </h2>
            <p className="text-sm text-industrial-400">
              Digital twin topology analysis and flow tracing
            </p>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setMode('trace')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
              mode === 'trace'
                ? 'bg-accent-blue text-industrial-950'
                : 'bg-industrial-700 text-industrial-300 hover:bg-industrial-600'
            }`}
          >
            Trace Flow Path
          </button>
          <button
            onClick={() => setMode('simulate')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
              mode === 'simulate'
                ? 'bg-accent-blue text-industrial-950'
                : 'bg-industrial-700 text-industrial-300 hover:bg-industrial-600'
            }`}
          >
            Simulate Valve
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="p-6 border-b border-industrial-600 bg-industrial-800">
        {mode === 'trace' ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-industrial-300 mb-2">
                Start Node
              </label>
              <select
                value={startNode}
                onChange={(e) => setStartNode(e.target.value)}
                className="w-full px-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue"
              >
                <option value="">Select a node...</option>
                {processingResult?.detections.map((det, idx) => (
                  <option key={idx} value={`node_${idx}`}>
                    {det.tag || `Node ${idx + 1}`} - {det.class_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-industrial-300 mb-2">
                Direction
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setDirection('downstream')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                    direction === 'downstream'
                      ? 'bg-accent-green text-industrial-950'
                      : 'bg-industrial-700 text-industrial-300'
                  }`}
                >
                  <ArrowRight className="w-4 h-4 inline mr-2" />
                  Downstream
                </button>
                <button
                  onClick={() => setDirection('upstream')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                    direction === 'upstream'
                      ? 'bg-accent-green text-industrial-950'
                      : 'bg-industrial-700 text-industrial-300'
                  }`}
                >
                  <ArrowRight className="w-4 h-4 inline mr-2 rotate-180" />
                  Upstream
                </button>
              </div>
            </div>

            <button
              onClick={handleTrace}
              disabled={!startNode || traceMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-accent-blue hover:bg-accent-blue/80 disabled:bg-industrial-600 disabled:cursor-not-allowed text-industrial-950 font-semibold rounded-lg transition-all"
            >
              {traceMutation.isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-industrial-950 border-t-transparent rounded-full animate-spin" />
                  Tracing...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Trace Flow Path
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-industrial-300 mb-2">
                Select Valve
              </label>
              <select
                value={selectedValve}
                onChange={(e) => setSelectedValve(e.target.value)}
                className="w-full px-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue"
              >
                <option value="">Select a valve...</option>
                {valveNodes.map((det, idx) => (
                  <option key={idx} value={det.tag || `valve_${idx}`}>
                    {det.tag || `Valve ${idx + 1}`} - {det.class_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-industrial-300 mb-2">
                Action
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setValveAction('close')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                    valveAction === 'close'
                      ? 'bg-accent-red text-industrial-950'
                      : 'bg-industrial-700 text-industrial-300'
                  }`}
                >
                  <Square className="w-4 h-4 inline mr-2" />
                  Close Valve
                </button>
                <button
                  onClick={() => setValveAction('open')}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                    valveAction === 'open'
                      ? 'bg-accent-green text-industrial-950'
                      : 'bg-industrial-700 text-industrial-300'
                  }`}
                >
                  <Play className="w-4 h-4 inline mr-2" />
                  Open Valve
                </button>
              </div>
            </div>

            <button
              onClick={handleSimulate}
              disabled={!selectedValve || simulateMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-accent-yellow hover:bg-accent-yellow/80 disabled:bg-industrial-600 disabled:cursor-not-allowed text-industrial-950 font-semibold rounded-lg transition-all"
            >
              {simulateMutation.isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-industrial-950 border-t-transparent rounded-full animate-spin" />
                  Simulating...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Simulate Valve Action
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-6">
        {mode === 'simulate' && simulationResult ? (
          <div className="space-y-4">
            {/* Simulation Results */}
            <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
              <h3 className="text-lg font-semibold text-industrial-200 mb-3">
                Simulation Results
              </h3>
              <div className="space-y-3">
                <InfoItem label="Valve ID" value={simulationResult.valve_id} />
                <InfoItem 
                  label="Action" 
                  value={simulationResult.action.toUpperCase()} 
                />
                <InfoItem 
                  label="Flow Status" 
                  value={simulationResult.flow_status} 
                />
              </div>
              
              <div className={`mt-4 p-3 rounded-lg border ${
                simulationResult.action === 'close' 
                  ? 'bg-accent-red/20 border-accent-red' 
                  : 'bg-accent-green/20 border-accent-green'
              }`}>
                <p className={`text-sm font-medium ${
                  simulationResult.action === 'close' 
                    ? 'text-accent-red' 
                    : 'text-accent-green'
                }`}>
                  {simulationResult.message}
                </p>
              </div>
            </div>

            {/* Affected Nodes */}
            {simulationResult.affected_nodes.length > 0 && (
              <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
                <h3 className="text-sm font-semibold text-industrial-300 mb-3">
                  Affected Nodes ({simulationResult.affected_nodes.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-auto">
                  {simulationResult.affected_nodes.map((node, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 bg-industrial-900 rounded"
                    >
                      <span className="w-6 h-6 flex items-center justify-center bg-accent-yellow text-industrial-950 rounded-full text-xs font-bold">
                        {idx + 1}
                      </span>
                      <span className="text-sm text-industrial-300 font-mono">
                        {node}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Visualization Hint */}
            <div className="bg-accent-yellow/10 border border-accent-yellow rounded-lg p-4">
              <p className="text-sm text-accent-yellow">
                💡 Switch to Canvas view to see the affected components highlighted
              </p>
            </div>
          </div>
        ) : mode === 'trace' && flowPath ? (
          <div className="space-y-4">
            {/* Path Info */}
            <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
              <h3 className="text-lg font-semibold text-industrial-200 mb-3">
                Flow Path Results
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <InfoItem label="Start Node" value={flowPath.start_node} />
                <InfoItem label="End Node" value={flowPath.end_node} />
                <InfoItem label="Total Nodes" value={flowPath.path_nodes.length.toString()} />
                <InfoItem label="Distance" value={`${flowPath.total_distance.toFixed(1)}px`} />
              </div>
              {flowPath.blocked_by && (
                <div className="mt-4 p-3 bg-accent-red/20 border border-accent-red rounded-lg">
                  <p className="text-accent-red text-sm font-medium">
                    <Square className="w-4 h-4 inline mr-2" />
                    Flow blocked by: {flowPath.blocked_by}
                  </p>
                </div>
              )}
            </div>

            {/* Path Nodes */}
            <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
              <h3 className="text-sm font-semibold text-industrial-300 mb-3">
                Path Nodes ({flowPath.path_nodes.length})
              </h3>
              <div className="space-y-2 max-h-64 overflow-auto">
                {flowPath.path_nodes.map((node, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 p-2 bg-industrial-900 rounded"
                  >
                    <span className="w-6 h-6 flex items-center justify-center bg-accent-blue text-industrial-950 rounded-full text-xs font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-sm text-industrial-300 font-mono">
                      {node}
                    </span>
                    {idx < flowPath.path_nodes.length - 1 && (
                      <ArrowRight className="w-4 h-4 text-industrial-500 ml-auto" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Visualization Hint */}
            <div className="bg-accent-blue/10 border border-accent-blue rounded-lg p-4">
              <p className="text-sm text-accent-blue">
                💡 Switch to Canvas view to see the highlighted flow path on the P&ID
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              {mode === 'trace' ? (
                <>
                  <Workflow className="w-16 h-16 text-industrial-600 mx-auto mb-4" />
                  <p className="text-industrial-400 mb-2">No flow path traced yet</p>
                  <p className="text-sm text-industrial-500">
                    Select a start node and click "Trace Flow Path"
                  </p>
                </>
              ) : (
                <>
                  <Zap className="w-16 h-16 text-industrial-600 mx-auto mb-4" />
                  <p className="text-industrial-400 mb-2">No simulation run yet</p>
                  <p className="text-sm text-industrial-500">
                    Select a valve and action, then click "Simulate Valve Action"
                  </p>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const InfoItem: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="text-xs text-industrial-500 mb-1">{label}</p>
    <p className="text-sm font-semibold text-industrial-200 font-mono">{value}</p>
  </div>
);
