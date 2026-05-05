/**
 * Natural Language Graph Filter Component
 * 
 * Allows users to filter graph nodes using natural language queries
 */

import React, { useState } from 'react';
import { Search, X, Loader2, Filter, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';

interface GraphFilterProps {
  topology: {
    nodes: any[];
    edges: any[];
  };
  onFilterApplied: (matchedNodeIds: string[], matchedEdgeIds: string[]) => void;
  onFilterCleared: () => void;
}

interface FilterResult {
  matched_node_ids: string[];
  matched_edge_ids: string[];
  explanation: string;
  query: string;
}

export const GraphFilter: React.FC<GraphFilterProps> = ({
  topology,
  onFilterApplied,
  onFilterCleared,
}) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState<FilterResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFilterActive, setIsFilterActive] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);

    try {
      const response = await axios.post<FilterResult>(
        'http://localhost:8000/api/filter-graph',
        {
          query: query.trim(),
          topology: topology,
        }
      );

      const filterResult = response.data;
      setResult(filterResult);
      setIsFilterActive(true);

      // Apply filter to graph
      onFilterApplied(filterResult.matched_node_ids, filterResult.matched_edge_ids);
    } catch (err: any) {
      console.error('Graph filtering failed:', err);
      
      let errorMessage = 'Failed to filter graph.';
      
      if (err.response?.status === 503) {
        errorMessage = 'AI service unavailable. Using fallback search.';
      } else if (err.response?.status === 500) {
        errorMessage = 'Backend error occurred.';
      } else if (err.code === 'ERR_NETWORK') {
        errorMessage = 'Cannot connect to backend.';
      }
      
      setError(errorMessage);
    } finally {
      setIsSearching(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResult(null);
    setError(null);
    setIsFilterActive(false);
    onFilterCleared();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isSearching) {
      handleSearch();
    }
  };

  // Quick filter suggestions
  const suggestions = [
    'all valves',
    'all pumps',
    'cooling water',
    'all instruments',
    'control valves',
  ];

  return (
    <div className="space-y-3">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-industrial-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="What do you want to see?"
          className="w-full pl-10 pr-4 py-2.5 bg-industrial-900/50 border border-industrial-600 rounded-xl text-industrial-100 placeholder-industrial-500 focus:outline-none focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all"
          disabled={isSearching}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        {!isFilterActive ? (
          <button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-accent-blue to-accent-cyan hover:from-accent-blue/80 hover:to-accent-cyan/80 disabled:from-industrial-600 disabled:to-industrial-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg"
          >
            {isSearching ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Eye className="w-4 h-4" />
                <span>Apply Filter</span>
              </>
            )}
          </button>
        ) : (
          <button
            onClick={handleClear}
            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg"
          >
            <EyeOff className="w-4 h-4" />
            <span>Clear Filter</span>
          </button>
        )}
      </div>

      {/* Quick Suggestions */}
      {!result && !error && (
        <div>
          <p className="text-xs text-industrial-400 mb-2">Quick filters:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => setQuery(suggestion)}
                className="px-3 py-1.5 bg-industrial-700/50 hover:bg-industrial-600 border border-industrial-600 hover:border-accent-blue/50 text-industrial-300 hover:text-industrial-100 text-xs rounded-lg transition-all"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-accent-blue/10 border border-accent-blue/30 rounded-xl p-3">
          <p className="text-sm text-industrial-200 mb-2">{result.explanation}</p>
          <div className="flex gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-accent-blue" />
              <span className="text-industrial-400">Nodes:</span>
              <span className="font-bold text-accent-blue">{result.matched_node_ids.length}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-accent-cyan" />
              <span className="text-industrial-400">Edges:</span>
              <span className="font-bold text-accent-cyan">{result.matched_edge_ids.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GraphFilter;
