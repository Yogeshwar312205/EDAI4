// API Type Definitions matching FastAPI backend

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface DetectionResult {
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  tag: string | null;
}

export interface GraphSummary {
  mode: string;
  [key: string]: any;
}

export interface ProcessingResult {
  image_name: string;
  processing_time_ms: number;
  layer1_detections: number;
  layer2_instruments: number;
  layer3_nodes: number;
  layer3_edges: number;
  detections: DetectionResult[];
  graph_summary: GraphSummary;
}

export interface GraphNode {
  id: string;
  type: string;
  tag: string | null;
  label: string;
  x: number;
  y: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface QueryRequest {
  question: string;
  use_llm?: boolean;
}

export interface QueryResponse {
  answer: string;
  confidence: number;
  sources: string[];
  intent: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  layers_ready: Record<string, boolean>;
  timestamp: string;
}
