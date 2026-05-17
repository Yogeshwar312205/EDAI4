/**
 * Text-to-Topology Panel - AI-Powered P&ID Drafting
 * 
 * Allows engineers to generate P&ID subsystems using natural language.
 * Powered by Gemini AI.
 */

import React, { useState } from 'react';
import { Sparkles, Wand2, Loader2, CheckCircle, XCircle, Lightbulb } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';

interface TextToTopologyPanelProps {
  onTopologyGenerated: (nodes: any[], edges: any[]) => void;
  existingNodes?: any[];
  existingEdges?: any[];
  startPosition?: { x: number; y: number };
}

interface GenerateTopologyRequest {
  prompt: string;
  existing_nodes?: any[];
  existing_edges?: any[];
  start_position?: { x: number; y: number };
}

interface GenerateTopologyResponse {
  nodes: any[];
  edges: any[];
  description: string;
  prompt: string;
  success: boolean;
  error?: string;
}

export const TextToTopologyPanel: React.FC<TextToTopologyPanelProps> = ({
  onTopologyGenerated,
  existingNodes = [],
  existingEdges = [],
  startPosition = { x: 100, y: 100 },
}) => {
  const [prompt, setPrompt] = useState('');
  const [generatedDescription, setGeneratedDescription] = useState('');

  // Mutation for topology generation
  const generateMutation = useMutation({
    mutationFn: async (request: GenerateTopologyRequest) => {
      const response = await api.post<GenerateTopologyResponse>(
        '/api/generate-topology',
        request
      );
      return response.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        setGeneratedDescription(data.description);
        onTopologyGenerated(data.nodes, data.edges);
      }
    },
    onError: (error: any) => {
      console.error('Topology generation error:', error);
    },
  });

  const handleGenerate = () => {
    if (!prompt.trim()) return;

    generateMutation.mutate({
      prompt: prompt.trim(),
      existing_nodes: existingNodes,
      existing_edges: existingEdges,
      start_position: startPosition,
    });
  };

  const handleExampleClick = (examplePrompt: string) => {
    setPrompt(examplePrompt);
  };

  const examples = [
    "Draft a cooling water return loop with two parallel centrifugal pumps and check valves",
    "Create a steam condensate system with level control and return pump",
    "Generate a chemical dosing system with metering pump and flow indicator",
    "Design a pressure relief system with PSV and rupture disk",
    "Build a heat exchanger loop with temperature control and bypass valve",
  ];

  return (
    <div className="h-full flex flex-col bg-industrial-900 rounded-lg border border-industrial-600">
      {/* Header */}
      <div className="p-6 border-b border-industrial-600 bg-gradient-to-r from-accent-purple/10 to-accent-blue/10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-accent-purple to-accent-blue rounded-lg flex items-center justify-center shadow-glow-purple">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-industrial-100">
              Text-to-Topology
            </h2>
            <p className="text-sm text-industrial-400">
              AI-Powered P&ID Drafting with Gemini
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Prompt Input */}
        <div>
          <label className="block text-sm font-medium text-industrial-300 mb-2">
            Describe Your Subsystem
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: Draft a cooling water return loop with two parallel centrifugal pumps and check valves..."
            className="w-full h-32 px-4 py-3 bg-industrial-800 border border-industrial-600 rounded-lg text-industrial-200 placeholder-industrial-500 focus:outline-none focus:border-accent-purple focus:ring-2 focus:ring-accent-purple/50 transition-all resize-none"
            disabled={generateMutation.isPending}
          />
          <p className="mt-2 text-xs text-industrial-500">
            Use natural language to describe equipment, instruments, and connections
          </p>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={!prompt.trim() || generateMutation.isPending}
          className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-accent-purple to-accent-blue hover:from-accent-purple/80 hover:to-accent-blue/80 disabled:from-industrial-600 disabled:to-industrial-600 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-accent-purple/50"
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating Topology...
            </>
          ) : (
            <>
              <Wand2 className="w-5 h-5" />
              Generate Topology
            </>
          )}
        </button>

        {/* Result */}
        {generateMutation.isSuccess && generateMutation.data && (
          <div className={`p-4 rounded-lg border ${
            generateMutation.data.success
              ? 'bg-accent-green/10 border-accent-green'
              : 'bg-accent-red/10 border-accent-red'
          }`}>
            <div className="flex items-start gap-3">
              {generateMutation.data.success ? (
                <CheckCircle className="w-6 h-6 text-accent-green flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-6 h-6 text-accent-red flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p className={`text-sm font-semibold mb-1 ${
                  generateMutation.data.success ? 'text-accent-green' : 'text-accent-red'
                }`}>
                  {generateMutation.data.success ? 'Topology Generated!' : 'Generation Failed'}
                </p>
                <p className={`text-sm ${
                  generateMutation.data.success ? 'text-accent-green/80' : 'text-accent-red/80'
                }`}>
                  {generateMutation.data.success
                    ? generatedDescription
                    : generateMutation.data.error || 'Unknown error'}
                </p>
                {generateMutation.data.success && (
                  <div className="mt-2 flex gap-4 text-xs text-industrial-400">
                    <span>
                      <strong className="text-accent-green">{generateMutation.data.nodes.length}</strong> nodes
                    </span>
                    <span>
                      <strong className="text-accent-cyan">{generateMutation.data.edges.length}</strong> edges
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {generateMutation.isError && (
          <div className="p-4 rounded-lg border bg-accent-red/10 border-accent-red">
            <div className="flex items-start gap-3">
              <XCircle className="w-6 h-6 text-accent-red flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-accent-red mb-1">
                  Error
                </p>
                <p className="text-sm text-accent-red/80">
                  {(generateMutation.error as any)?.response?.data?.detail ||
                    (generateMutation.error as any)?.message ||
                    'Failed to generate topology'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Examples */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-accent-yellow" />
            <h3 className="text-sm font-semibold text-industrial-300">
              Example Prompts
            </h3>
          </div>
          <div className="space-y-2">
            {examples.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                disabled={generateMutation.isPending}
                className="w-full text-left px-4 py-3 bg-industrial-800 hover:bg-industrial-700 border border-industrial-600 hover:border-accent-purple rounded-lg transition-all text-sm text-industrial-300 hover:text-industrial-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {/* Tips */}
        <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
          <h3 className="text-sm font-semibold text-industrial-300 mb-2">
            💡 Tips for Better Results
          </h3>
          <ul className="space-y-1 text-xs text-industrial-400">
            <li>• Be specific about equipment types (centrifugal pump, gate valve, etc.)</li>
            <li>• Mention control requirements (level control, flow control, etc.)</li>
            <li>• Specify parallel or series configurations</li>
            <li>• Include safety devices (check valves, relief valves, etc.)</li>
            <li>• Describe the process flow direction</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TextToTopologyPanel;
