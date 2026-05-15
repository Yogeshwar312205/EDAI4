/**
 * Node Label Component
 * Multi-line label with hierarchy: Type → Tag → ID
 */

import React from 'react';
import { NodeIcon } from './NodeIcon';
import { getNodeTypeName, truncateLabel } from '@/utils/nodeUtils';

interface NodeLabelProps {
  type: string;
  tag?: string;
  label?: string;
  nodeId: string;
  showId?: boolean;
  compact?: boolean;
}

export const NodeLabel: React.FC<NodeLabelProps> = ({
  type,
  tag,
  label,
  nodeId,
  showId = true,
  compact = false,
}) => {
  const typeName = getNodeTypeName(type);
  const displayTag = tag || label || 'UNTAGGED';
  const truncatedType = truncateLabel(typeName, 12);

  if (compact) {
    // Compact mode for small nodes or zoomed out
    return (
      <div className="flex flex-col items-center justify-center gap-0.5 text-center">
        <div className="flex items-center gap-1">
          <NodeIcon type={type} size={14} />
          <span className="text-xs font-semibold">{displayTag}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-1 text-center w-full">
      {/* Line 1: Icon + Type */}
      <div className="flex items-center gap-1.5 text-white/90">
        <NodeIcon type={type} size={16} />
        <span className="text-[11px] font-semibold tracking-wide">
          {truncatedType}
        </span>
      </div>

      {/* Line 2: Tag (Prominent) */}
      <div className="text-[14px] font-bold text-white leading-tight tracking-wide">
        {displayTag}
      </div>

      {/* Line 3: System ID (Optional) */}
      {showId && (
        <div className="text-[9px] font-normal text-white/60 font-mono">
          #{nodeId.split('-').pop() || nodeId.substring(0, 8)}
        </div>
      )}
    </div>
  );
};

export default NodeLabel;
