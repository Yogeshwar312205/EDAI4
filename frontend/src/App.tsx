// Main Application Component
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactFlowProvider } from 'reactflow';
import { useAppStore } from '@/store/useAppStore';
import { FileUpload } from '@/components/FileUpload';
import { InteractiveCanvas } from '@/components/InteractiveCanvas';
import { DataTable } from '@/components/DataTable';
import { GraphViewer } from '@/components/GraphViewer';
import { DeliverablesPanel } from '@/components/DeliverablesPanel';
import { DesignRulesDashboard } from '@/components/DesignRulesDashboard';
import { FlowSimulator } from '@/components/FlowSimulator';
import { HazOpSimulator } from '@/components/HazOpSimulator';
import { HazOpSimulatorWrapper } from '@/components/HazOpSimulatorWrapper';
import { HazOpTest } from '@/components/HazOpTest';
import { Layers, Table, Network, Upload as UploadIcon, FileText, Shield, Workflow, AlertTriangle } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const {
    uploadedImage,
    processingResult,
    graphData,
    activeView,
    setActiveView,
  } = useAppStore();

  const hasData = processingResult !== null;

  // Debug logging
  console.log('AppContent render - activeView:', activeView);
  console.log('AppContent render - graphData:', graphData);
  console.log('AppContent render - hasData:', hasData);

  return (
    <div className="min-h-screen bg-industrial-950 text-industrial-200">
      {/* Header */}
      <header className="bg-industrial-900 border-b border-industrial-700 shadow-lg">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-accent-blue to-accent-cyan rounded-lg flex items-center justify-center shadow-glow-blue">
                <Layers className="w-7 h-7 text-industrial-950" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-industrial-100">
                  EDAI4 Dashboard
                </h1>
                <p className="text-sm text-industrial-400 font-mono">
                  Hybrid Perception Pipeline - P&ID Intelligence
                </p>
              </div>
            </div>
            
            {/* View Tabs */}
            {hasData && (
              <div className="flex gap-2 bg-industrial-800 p-1 rounded-lg border border-industrial-600">
                <TabButton
                  icon={<Layers className="w-4 h-4" />}
                  label="Canvas"
                  active={activeView === 'canvas'}
                  onClick={() => setActiveView('canvas')}
                />
                <TabButton
                  icon={<Network className="w-4 h-4" />}
                  label="Graph"
                  active={activeView === 'graph'}
                  onClick={() => setActiveView('graph')}
                />
                <TabButton
                  icon={<FileText className="w-4 h-4" />}
                  label="Deliverables"
                  active={activeView === 'deliverables'}
                  onClick={() => setActiveView('deliverables')}
                />
                <TabButton
                  icon={<Shield className="w-4 h-4" />}
                  label="Design Rules"
                  active={activeView === 'rules'}
                  onClick={() => setActiveView('rules')}
                />
                <TabButton
                  icon={<Workflow className="w-4 h-4" />}
                  label="Flow Sim"
                  active={activeView === 'flow'}
                  onClick={() => setActiveView('flow')}
                />
                <TabButton
                  icon={<AlertTriangle className="w-4 h-4" />}
                  label="HazOp"
                  active={activeView === 'hazop'}
                  onClick={() => setActiveView('hazop')}
                />
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-6">
        {!hasData ? (
          /* Upload View */
          <div className="max-w-3xl mx-auto mt-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-industrial-100 mb-3">
                Welcome to EDAI4
              </h2>
              <p className="text-industrial-400">
                Upload a P&ID diagram to extract instruments, analyze topology, and query with natural language
              </p>
            </div>
            <FileUpload />
            
            {/* Features Preview */}
            <div className="mt-12 grid grid-cols-3 gap-6">
              <FeatureCard
                icon={<Layers className="w-8 h-8" />}
                title="Interactive Canvas"
                description="Pan, zoom, and explore detected symbols with real-time highlighting"
              />
              <FeatureCard
                icon={<Table className="w-8 h-8" />}
                title="Smart Data Table"
                description="Sort, filter, and click to zoom directly to any detection"
              />
              <FeatureCard
                icon={<Network className="w-8 h-8" />}
                title="Knowledge Graph"
                description="Visualize topology and relationships with physics-based layout"
              />
            </div>
          </div>
        ) : (
          /* Analysis View */
          <div className={`grid gap-6 h-[calc(100vh-180px)] ${
            activeView === 'canvas' ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'
          }`}>
            {/* Main View - Full width for graph/deliverables/rules/flow/hazop, 2/3 for canvas */}
            <div className={`h-full overflow-hidden ${
              activeView === 'canvas' ? 'lg:col-span-2' : 'col-span-1'
            }`}>
              {activeView === 'canvas' && uploadedImage && processingResult ? (
                <InteractiveCanvas
                  imageUrl={uploadedImage}
                  detections={processingResult.detections}
                  imageSize={{ width: 1200, height: 800 }}
                />
              ) : activeView === 'graph' ? (
                graphData && graphData.nodes && graphData.nodes.length > 0 ? (
                  <ReactFlowProvider>
                    <GraphViewer graphData={graphData} />
                  </ReactFlowProvider>
                ) : (
                  <EmptyState message="No Graph Data Available" />
                )
              ) : activeView === 'deliverables' ? (
                <DeliverablesPanel />
              ) : activeView === 'rules' ? (
                <DesignRulesDashboard />
              ) : activeView === 'flow' ? (
                <FlowSimulator />
              ) : activeView === 'hazop' ? (
                <div className="w-full h-full">
                  {!graphData || !graphData.nodes || graphData.nodes.length === 0 ? (
                    <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
                      <div className="text-center p-8 max-w-md">
                        <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
                        <h3 className="text-xl font-bold text-industrial-100 mb-2">No Graph Data Available</h3>
                        <p className="text-industrial-400 mb-4">
                          Please upload and process a P&ID first to generate the graph data needed for HazOp simulation.
                        </p>
                        <div className="text-left bg-industrial-900 p-4 rounded text-xs font-mono">
                          <p className="text-industrial-500">Debug Info:</p>
                          <p>graphData: {graphData ? 'exists' : 'null'}</p>
                          {graphData && (
                            <>
                              <p>nodes: {graphData.nodes ? `array[${graphData.nodes.length}]` : 'null'}</p>
                              <p>edges: {graphData.edges ? `array[${graphData.edges.length}]` : 'null'}</p>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <ReactFlowProvider>
                      <HazOpSimulator
                        initialNodes={graphData.nodes.map((node: any, index: number) => ({
                          ...node,
                          type: 'custom',  // Use custom node type
                          position: node.position || { 
                            x: (index % 5) * 200 + 100, 
                            y: Math.floor(index / 5) * 150 + 100 
                          },
                          data: {
                            ...node.data,
                            label: node.data?.label || node.id,
                            type: node.type || node.data?.type || 'equipment',
                            tag: node.data?.tag || node.id,
                            description: node.data?.description || `Equipment node ${node.id}`,
                            status: 'normal'
                          },
                          style: {
                            ...node.style
                          }
                        }))}
                        initialEdges={(graphData.edges || []).map((edge: any) => ({
                          ...edge,
                          type: 'smoothstep',
                          animated: false,
                          style: {
                            stroke: '#61afef',
                            strokeWidth: 2,
                            ...edge.style
                          },
                          labelStyle: {
                            fill: '#abb2bf',
                            fontSize: 12
                          },
                          labelBgStyle: {
                            fill: '#1a1f29',
                            fillOpacity: 0.9
                          }
                        }))}
                      />
                    </ReactFlowProvider>
                  )}
                </div>
              ) : (
                <EmptyState message="No data available" />
              )}
            </div>

            {/* Right: Data Table (1/3 width) - Only show for canvas view */}
            {activeView === 'canvas' && (
              <div className="h-full overflow-hidden">
                {processingResult && (
                  <DataTable detections={processingResult.detections} />
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-industrial-900/80 backdrop-blur-sm border-t border-industrial-700 py-2 px-6">
        <div className="container mx-auto flex items-center justify-between text-xs text-industrial-400 font-mono">
          <div>EDAI4 v1.0.0 | 5-Layer Hybrid Pipeline</div>
          {processingResult && (
            <div className="flex gap-6">
              <span>Mode: {processingResult.graph_summary.mode}</span>
              <span>Processing: {processingResult.processing_time_ms.toFixed(0)}ms</span>
              <span>Detections: {processingResult.layer1_detections}</span>
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}

// Helper Components
const TabButton: React.FC<{
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}> = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`
      flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-all
      ${
        active
          ? 'bg-accent-blue text-industrial-950 shadow-glow-blue'
          : 'text-industrial-300 hover:text-industrial-100 hover:bg-industrial-700'
      }
    `}
  >
    {icon}
    {label}
  </button>
);

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
    <div className="text-center text-industrial-400">
      <UploadIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
      <p>{message}</p>
    </div>
  </div>
);

const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <div className="bg-industrial-800 rounded-lg p-6 border border-industrial-600 hover:border-accent-blue transition-colors">
    <div className="text-accent-blue mb-3">{icon}</div>
    <h3 className="text-lg font-semibold text-industrial-100 mb-2">{title}</h3>
    <p className="text-sm text-industrial-400">{description}</p>
  </div>
);

// Main App with Providers
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
