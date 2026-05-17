// Zustand Store for Cross-Component State Management
import { create } from 'zustand';
import type { ProcessingResult, GraphData, DetectionResult } from '@/types/api';

interface FlowSimulationResult {
  active_node_ids: string[];
  active_edge_ids: string[];
  blocked_nodes: string[];
  flow_path: string[];
  total_distance: number;
  message: string;
}

interface AppState {
  // Image and processing data
  uploadedImage: string | null;
  processingResult: ProcessingResult | null;
  graphData: GraphData | null;
  
  // UI state
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
  activeView: 'canvas' | 'graph' | 'deliverables' | 'rules' | 'flow' | 'hazop' | 'editor' | 'history';
  
  // Flow simulation state
  flowSimulationResult: FlowSimulationResult | null;
  
  // Actions
  setUploadedImage: (image: string | null) => void;
  setProcessingResult: (result: ProcessingResult | null) => void;
  setGraphData: (data: GraphData | null) => void;
  setSelectedNodeId: (id: string | null) => void;
  setHoveredNodeId: (id: string | null) => void;
  setActiveView: (view: 'canvas' | 'graph' | 'deliverables' | 'rules' | 'flow' | 'hazop' | 'editor' | 'history') => void;
  setFlowSimulationResult: (result: FlowSimulationResult | null) => void;
  
  // Computed getters
  getDetectionById: (id: string) => DetectionResult | undefined;
  reset: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  uploadedImage: null,
  processingResult: null,
  graphData: null,
  selectedNodeId: null,
  hoveredNodeId: null,
  activeView: 'canvas',
  flowSimulationResult: null,
  
  // Actions
  setUploadedImage: (image) => set({ uploadedImage: image }),
  
  setProcessingResult: (result) => set({ processingResult: result }),
  
  setGraphData: (data) => set({ graphData: data }),
  
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  
  setHoveredNodeId: (id) => set({ hoveredNodeId: id }),
  
  setActiveView: (view) => set({ activeView: view }),
  
  setFlowSimulationResult: (result) => set({ flowSimulationResult: result }),
  
  // Computed getters
  getDetectionById: (id: string) => {
    const result = get().processingResult;
    if (!result) return undefined;
    
    const index = parseInt(id.replace('node_', ''));
    return result.detections[index];
  },
  
  reset: () => set({
    uploadedImage: null,
    processingResult: null,
    graphData: null,
    selectedNodeId: null,
    hoveredNodeId: null,
    activeView: 'canvas',
    flowSimulationResult: null,
  }),
}));
