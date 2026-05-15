/**
 * Enhanced Node Component
 * Custom ReactFlow node with improved labels, icons, and tooltips
 */

import { memo, useState, useMemo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { NodeLabel } from './NodeLabel';
import { NodeTooltip } from './NodeTooltip';
import { getNodeStyle } from '@/utils/nodeUtils';

interface EnhancedNodeData {
  label?: string;
  type: string;
  tag?: string;
  description?: string;
  status?: 'normal' | 'warning' | 'danger' | 'critical';
}

export const EnhancedNode = memo(({ 
  id, 
  data, 
  selected,
  xPos,
  yPos,
}: NodeProps<EnhancedNodeData>) => {
  const [isHovered, setIsHovered] = useState(false);

  // Get node style based on type and selection
  const nodeStyle = useMemo(
    () => getNodeStyle(data.type, selected),
    [data.type, selected]
  );

  // Determine if we should show compact mode
  const compact = false; // Can be based on zoom level in future

  return (
    <div
      className="relative group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={nodeStyle}
    >
      {/* Connection Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-accent-blue border-2 border-white"
        style={{ left: -6 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-accent-cyan border-2 border-white"
        style={{ right: -6 }}
      />

      {/* Node Content */}
      <div className="flex flex-col items-center justify-center min-h-[56px]">
        <NodeLabel
          type={data.type}
          tag={data.tag}
          label={data.label}
          nodeId={id}
          showId={true}
          compact={compact}
        />
      </div>

      {/* Status Indicator */}
      {data.status && data.status !== 'normal' && (
        <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full border-2 border-white flex items-center justify-center text-[10px]">
          {data.status === 'critical' && (
            <div className="w-full h-full rounded-full bg-red-500 animate-pulse" />
          )}
          {data.status === 'danger' && (
            <div className="w-full h-full rounded-full bg-orange-500" />
          )}
          {data.status === 'warning' && (
            <div className="w-full h-full rounded-full bg-yellow-500" />
          )}
        </div>
      )}

      {/* Hover Tooltip */}
      <NodeTooltip
        type={data.type}
        tag={data.tag}
        label={data.label}
        nodeId={id}
        position={{ x: xPos, y: yPos }}
        show={isHovered && !selected}
      />

      {/* Selection Indicator */}
      {selected && (
        <div className="absolute inset-0 rounded-lg pointer-events-none">
          <div className="absolute inset-0 rounded-lg border-2 border-white/30 animate-pulse" />
        </div>
      )}
    </div>
  );
});

EnhancedNode.displayName = 'EnhancedNode';

export default EnhancedNode;
