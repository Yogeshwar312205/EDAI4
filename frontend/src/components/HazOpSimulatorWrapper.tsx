/**
 * HazOp Simulator Wrapper with Debug Info
 * Helps diagnose blank screen issues
 */

import React from 'react';
import { ReactFlowProvider } from 'reactflow';
import { HazOpSimulator } from './HazOpSimulator';
import { AlertTriangle } from 'lucide-react';

interface HazOpSimulatorWrapperProps {
  graphData: any;
}

export const HazOpSimulatorWrapper: React.FC<HazOpSimulatorWrapperProps> = ({ graphData }) => {
  // Debug logging
  console.log('HazOpSimulatorWrapper - graphData:', graphData);
  console.log('HazOpSimulatorWrapper - nodes:', graphData?.nodes);
  console.log('HazOpSimulatorWrapper - edges:', graphData?.edges);

  // Check if graphData exists
  if (!graphData) {
    return (
      <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
        <div className="text-center text-industrial-400 max-w-md p-8">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
          <h3 className="text-xl font-bold text-industrial-100 mb-2">No Graph Data</h3>
          <p className="mb-4">
            Graph data is not available. Please make sure you've processed a P&ID and generated the graph.
          </p>
          <div className="text-left bg-industrial-900 p-4 rounded text-xs font-mono">
            <p className="text-industrial-500">Debug Info:</p>
            <p className="text-red-400">graphData: null or undefined</p>
          </div>
        </div>
      </div>
    );
  }

  // Check if nodes exist
  if (!graphData.nodes || !Array.isArray(graphData.nodes)) {
    return (
      <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
        <div className="text-center text-industrial-400 max-w-md p-8">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
          <h3 className="text-xl font-bold text-industrial-100 mb-2">Invalid Graph Structure</h3>
          <p className="mb-4">
            Graph data exists but doesn't have a valid nodes array.
          </p>
          <div className="text-left bg-industrial-900 p-4 rounded text-xs font-mono">
            <p className="text-industrial-500">Debug Info:</p>
            <p className="text-yellow-400">graphData exists: true</p>
            <p className="text-red-400">graphData.nodes: {typeof graphData.nodes}</p>
            <p className="text-industrial-300">Expected: array</p>
          </div>
        </div>
      </div>
    );
  }

  // Check if nodes array is empty
  if (graphData.nodes.length === 0) {
    return (
      <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
        <div className="text-center text-industrial-400 max-w-md p-8">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
          <h3 className="text-xl font-bold text-industrial-100 mb-2">Empty Graph</h3>
          <p className="mb-4">
            Graph data exists but contains no nodes. The P&ID processing may not have detected any equipment.
          </p>
          <div className="text-left bg-industrial-900 p-4 rounded text-xs font-mono">
            <p className="text-industrial-500">Debug Info:</p>
            <p className="text-yellow-400">graphData.nodes.length: 0</p>
            <p className="text-yellow-400">graphData.edges.length: {graphData.edges?.length || 0}</p>
          </div>
        </div>
      </div>
    );
  }

  // Check if edges exist
  if (!graphData.edges || !Array.isArray(graphData.edges)) {
    console.warn('HazOpSimulator: edges is not an array, using empty array');
    graphData.edges = [];
  }

  // All checks passed, render the simulator
  console.log(`HazOpSimulator: Rendering with ${graphData.nodes.length} nodes and ${graphData.edges.length} edges`);

  return (
    <ReactFlowProvider>
      <HazOpSimulator
        initialNodes={graphData.nodes}
        initialEdges={graphData.edges}
      />
    </ReactFlowProvider>
  );
};

export default HazOpSimulatorWrapper;
