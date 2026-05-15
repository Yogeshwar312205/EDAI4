/**
 * Node Icon Component
 * Displays icon for node type
 */

import React from 'react';
import { getNodeIcon } from '@/utils/nodeUtils';

interface NodeIconProps {
  type: string;
  size?: number;
  className?: string;
}

export const NodeIcon: React.FC<NodeIconProps> = ({ 
  type, 
  size = 16, 
  className = '' 
}) => {
  const IconComponent = getNodeIcon(type);
  
  return (
    <IconComponent 
      className={`inline-block ${className}`} 
      size={size}
      strokeWidth={2.5}
    />
  );
};

export default NodeIcon;
