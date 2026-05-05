// Zustand Store for Cross-Component State Management
import { create } from 'zustand';
import type { ProcessingResult, GraphData, DetectionResult } from '@/types/api';

interface AppState {
  // Image and processing data
  uploadedImage: string | null;
  processingResult: ProcessingResult | null;
  graphData: GraphData | null;
  
  // UI state
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
  activeView: 'canvas' | 'graph' | 'deliverables' | 'rules' | 'flow' | 'hazop';
  
  // Actions
  setUploadedImage: (image: string | null) => void;
  setProcessingResult: (result: ProcessingResult | null) => void;
  setGraphData: (data: GraphData | null) => void;
  setSelectedNodeId: (id: string | null) => void;
  setHoveredNodeId: (id: string | null) => void;
  setActiveView: (view: 'canvas' | 'graph' | 'deliverables' | 'rules' | 'flow' | 'hazop') => void;
  
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
  
  // Actions
  setUploadedImage: (image) => set({ uploadedImage: image }),
  
  setProcessingResult: (result) => set({ processingResult: result }),
  
  setGraphData: (data) => set({ graphData: data }),
  
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  
  setHoveredNodeId: (id) => set({ hoveredNodeId: id }),
  
  setActiveView: (view) => set({ activeView: view }),
  
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
  }),
}));
