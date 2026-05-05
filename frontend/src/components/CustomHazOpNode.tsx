/**
 * Custom Node Component for HazOp Simulator
 * Shows detailed equipment information
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { AlertCircle, Zap, Droplet, Wind } from 'lucide-react';

interface CustomNodeData {
  label?: string;
  type?: string;
  tag?: string;
  description?: string;
  status?: 'normal' | 'warning' | 'danger' | 'critical';
}

export const CustomHazOpNode = memo(({ data, selected }: NodeProps<CustomNodeData>) => {
  const getIcon = () => {
    const type = data.type?.toLowerCase() || '';
    if (type.includes('valve')) return <Droplet className="w-4 h-4" />;
    if (type.includes('pump')) return <Wind className="w-4 h-4" />;
    if (type.includes('tank')) return <AlertCircle className="w-4 h-4" />;
    return <Zap className="w-4 h-4" />;
  };

  const getStatusColor = () => {
    switch (data.status) {
      case 'critical': return 'border-red-500 bg-red-500/10';
      case 'danger': return 'border-orange-500 bg-orange-500/10';
      case 'warning': return 'border-yellow-500 bg-yellow-500/10';
      default: return 'border-industrial-500 bg-industrial-800';
    }
  };

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 transition-all duration-200
        ${getStatusColor()}
        ${selected ? 'ring-2 ring-accent-blue shadow-lg shadow-accent-blue/30' : ''}
        hover:shadow-lg hover:scale-105
        min-w-[160px]
      `}
    >
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-accent-blue border-2 border-industrial-900"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-accent-cyan border-2 border-industrial-900"
      />

      {/* Content */}
      <div className="flex items-start gap-2">
        <div className="text-accent-blue mt-0.5">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          {/* Tag/ID */}
          {data.tag && (
            <div className="text-xs font-bold text-accent-cyan font-mono mb-1">
              {data.tag}
            </div>
          )}
          
          {/* Label */}
          <div className="text-sm font-semibold text-industrial-100 leading-tight mb-1">
            {data.label || 'Unknown Equipment'}
          </div>
          
          {/* Type */}
          {data.type && (
            <div className="text-xs text-industrial-400 capitalize">
              {data.type}
            </div>
          )}
          
          {/* Description */}
          {data.description && (
            <div className="text-xs text-industrial-500 mt-1 line-clamp-2">
              {data.description}
            </div>
          )}
        </div>
      </div>

      {/* Status Indicator */}
      {data.status && data.status !== 'normal' && (
        <div className="mt-2 pt-2 border-t border-industrial-600">
          <div className={`
            text-xs font-bold uppercase tracking-wide
            ${data.status === 'critical' ? 'text-red-400' : ''}
            ${data.status === 'danger' ? 'text-orange-400' : ''}
            ${data.status === 'warning' ? 'text-yellow-400' : ''}
          `}>
            ⚠ {data.status}
          </div>
        </div>
      )}
    </div>
  );
});

CustomHazOpNode.displayName = 'CustomHazOpNode';

export default CustomHazOpNode;
