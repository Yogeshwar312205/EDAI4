/**
 * Node Tooltip Component
 * Shows detailed information on hover
 */

import React, { useState, useEffect } from 'react';
import { getNodeTypeName, getISATagDescription, parseISATag } from '@/utils/nodeUtils';

interface NodeTooltipProps {
  type: string;
  tag?: string;
  label?: string;
  nodeId: string;
  position: { x: number; y: number };
  connectionCount?: { incoming: number; outgoing: number };
  show: boolean;
}

export const NodeTooltip: React.FC<NodeTooltipProps> = ({
  type,
  tag,
  label,
  nodeId,
  position,
  connectionCount,
  show,
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (show) {
      // Delay tooltip appearance by 300ms
      const timer = setTimeout(() => setVisible(true), 300);
      return () => clearTimeout(timer);
    } else {
      setVisible(false);
    }
  }, [show]);

  if (!visible) return null;

  const typeName = getNodeTypeName(type);
  const displayTag = tag || label || 'UNTAGGED';
  const tagParts = tag ? parseISATag(tag) : null;
  const tagDescription = tag && tagParts ? getISATagDescription(tag) : null;

  return (
    <div
      className="absolute z-[9999] pointer-events-none"
      style={{
        left: '50%',
        top: '100%',
        transform: 'translateX(-50%)',
        marginTop: '8px',
      }}
    >
      <div className="bg-industrial-900/95 backdrop-blur-md border border-industrial-600 rounded-lg shadow-2xl p-3 min-w-[220px] animate-fade-in">
        {/* Header */}
        {tagDescription && (
          <div className="text-sm font-bold text-industrial-100 mb-2 pb-2 border-b border-industrial-700">
            {tagDescription}
          </div>
        )}

        {/* Details */}
        <div className="space-y-1.5 text-xs font-mono">
          {/* Tag */}
          <div className="flex items-center gap-2">
            <span className="text-industrial-500">📋 Tag:</span>
            <span className="text-accent-cyan font-bold">{displayTag}</span>
          </div>

          {/* Type */}
          <div className="flex items-center gap-2">
            <span className="text-industrial-500">🏷️  Type:</span>
            <span className="text-industrial-200 capitalize">{typeName}</span>
          </div>

          {/* ID */}
          <div className="flex items-center gap-2">
            <span className="text-industrial-500">🆔 ID:</span>
            <span className="text-industrial-300 truncate max-w-[140px]" title={nodeId}>
              {nodeId}
            </span>
          </div>

          {/* Position */}
          <div className="flex items-center gap-2">
            <span className="text-industrial-500">📍 Pos:</span>
            <span className="text-industrial-300">
              ({Math.round(position.x)}, {Math.round(position.y)})
            </span>
          </div>

          {/* Connections */}
          {connectionCount && (
            <div className="flex items-center gap-2">
              <span className="text-industrial-500">🔗 Conn:</span>
              <span className="text-industrial-300">
                {connectionCount.incoming} in, {connectionCount.outgoing} out
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NodeTooltip;
