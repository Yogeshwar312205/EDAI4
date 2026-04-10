// Main Application Component
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAppStore } from '@/store/useAppStore';
import { FileUpload } from '@/components/FileUpload';
import { InteractiveCanvas } from '@/components/InteractiveCanvas';
import { DataTable } from '@/components/DataTable';
import { GraphViewer } from '@/components/GraphViewer';
import { Layers, Table, Network, Upload as UploadIcon } from 'lucide-react';

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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">
            {/* Left: Canvas or Graph (2/3 width) */}
            <div className="lg:col-span-2 h-full overflow-hidden">
              {activeView === 'canvas' && uploadedImage && processingResult ? (
                <InteractiveCanvas
                  imageUrl={uploadedImage}
                  detections={processingResult.detections}
                  imageSize={{ width: 1200, height: 800 }} // Will be dynamic from backend
                />
              ) : activeView === 'graph' ? (
                graphData && graphData.nodes && graphData.nodes.length > 0 ? (
                  <GraphViewer graphData={graphData} />
                ) : (
                  <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
                    <div className="text-center text-industrial-400">
                      <UploadIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg mb-2">No Graph Data Available</p>
                      <p className="text-sm">Process a P&ID image to generate topology graph</p>
                    </div>
                  </div>
                )
              ) : (
                <div className="w-full h-full bg-industrial-800 rounded-lg border border-industrial-600 flex items-center justify-center">
                  <div className="text-center text-industrial-400">
                    <UploadIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No data available</p>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Data Table (1/3 width) */}
            <div className="h-full overflow-hidden">
              {processingResult && (
                <DataTable detections={processingResult.detections} />
              )}
            </div>
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
