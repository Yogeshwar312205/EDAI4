/**
 * Legend Component for HazOp Simulator
 * Helps users understand the visual indicators
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';

export const HazOpLegend: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="fixed bottom-6 left-6 z-40 max-w-xs">
      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full bg-industrial-800 border border-industrial-600 rounded-lg px-4 py-2 flex items-center justify-between hover:bg-industrial-700 transition-colors"
      >
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-accent-blue" />
          <span className="text-sm font-semibold text-industrial-100">Legend</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-industrial-400" />
        ) : (
          <ChevronUp className="w-4 h-4 text-industrial-400" />
        )}
      </button>

      {/* Legend Content */}
      {isExpanded && (
        <div className="mt-2 bg-industrial-800 border border-industrial-600 rounded-lg p-4 shadow-lg animate-fade-in">
          <div className="space-y-3">
            {/* Node States */}
            <div>
              <div className="text-xs font-bold text-industrial-300 uppercase tracking-wide mb-2">
                Node States
              </div>
              <div className="space-y-2">
                <LegendItem
                  color="bg-industrial-600"
                  label="Normal"
                  description="Equipment operating normally"
                />
                <LegendItem
                  color="bg-red-500"
                  label="Failed"
                  description="Equipment has failed (pulsing)"
                />
                <LegendItem
                  color="bg-orange-500"
                  label="Affected"
                  description="Equipment in danger zone"
                />
              </div>
            </div>

            {/* Edge States */}
            <div className="pt-3 border-t border-industrial-600">
              <div className="text-xs font-bold text-industrial-300 uppercase tracking-wide mb-2">
                Connection States
              </div>
              <div className="space-y-2">
                <LegendItem
                  color="bg-accent-blue"
                  label="Normal"
                  description="Normal flow/connection"
                />
                <LegendItem
                  color="bg-red-500"
                  label="Critical"
                  description="Abnormal conditions (animated)"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="pt-3 border-t border-industrial-600">
              <div className="text-xs font-bold text-industrial-300 uppercase tracking-wide mb-2">
                Actions
              </div>
              <div className="space-y-1 text-xs text-industrial-400">
                <div>• <span className="text-industrial-200">Right-click</span> node to simulate failure</div>
                <div>• <span className="text-industrial-200">Scroll</span> to zoom in/out</div>
                <div>• <span className="text-industrial-200">Drag</span> to pan canvas</div>
                <div>• <span className="text-industrial-200">Click</span> node to select</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const LegendItem: React.FC<{ color: string; label: string; description: string }> = ({
  color,
  label,
  description,
}) => (
  <div className="flex items-center gap-2">
    <div className={`w-3 h-3 rounded ${color}`} />
    <div className="flex-1">
      <div className="text-xs font-semibold text-industrial-100">{label}</div>
      <div className="text-xs text-industrial-500">{description}</div>
    </div>
  </div>
);

export default HazOpLegend;
