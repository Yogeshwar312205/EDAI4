/**
 * Node Utilities
 * Helper functions for node styling, ISA tags, and icons
 */

import { Gauge, Wrench, Cog, Package, Zap } from 'lucide-react';

// Node type to icon mapping
export const NODE_ICONS = {
  instrument: Gauge,
  valve: Wrench,
  pump: Cog,
  equipment: Package,
  other: Zap,
} as const;

// Node type to color mapping
export const NODE_COLORS = {
  instrument: '#61afef',
  valve: '#56b6c2',
  pump: '#e5c07b',
  equipment: '#98c379',
  other: '#c678dd',
} as const;

// Node dimensions
export const NODE_DIMENSIONS = {
  minWidth: 140,
  minHeight: 80,
  padding: 12,
  borderRadius: 8,
  borderWidth: 2,
} as const;

/**
 * Get icon component for node type
 */
export function getNodeIcon(type: string) {
  const lowerType = type.toLowerCase();
  if (lowerType.includes('instrument')) return NODE_ICONS.instrument;
  if (lowerType.includes('valve')) return NODE_ICONS.valve;
  if (lowerType.includes('pump')) return NODE_ICONS.pump;
  if (lowerType.includes('equipment')) return NODE_ICONS.equipment;
  return NODE_ICONS.other;
}

/**
 * Get color for node type
 */
export function getNodeColor(type: string): string {
  const lowerType = type.toLowerCase();
  if (lowerType.includes('instrument')) return NODE_COLORS.instrument;
  if (lowerType.includes('valve')) return NODE_COLORS.valve;
  if (lowerType.includes('pump')) return NODE_COLORS.pump;
  if (lowerType.includes('equipment')) return NODE_COLORS.equipment;
  return NODE_COLORS.other;
}

/**
 * Get display name for node type
 */
export function getNodeTypeName(type: string): string {
  const lowerType = type.toLowerCase();
  if (lowerType.includes('instrument')) return 'Instrument';
  if (lowerType.includes('valve')) return 'Valve';
  if (lowerType.includes('pump')) return 'Pump';
  if (lowerType.includes('equipment')) return 'Equipment';
  return 'Component';
}

/**
 * Validate ISA tag format
 * Format: [A-Z][A-Z]*-\d+[A-Z]?
 * Examples: FIC-101, PT-205A, TIC-301
 */
export function validateISATag(tag: string): boolean {
  const regex = /^[A-Z][A-Z]*-\d+[A-Z]?$/;
  return regex.test(tag);
}

/**
 * Parse ISA tag into components
 */
export interface ISATagParts {
  measuredVariable: string;  // F, P, T, L, etc.
  modifiers: string[];       // I, C, V, etc.
  loopNumber: number;        // 101, 102, etc.
  suffix?: string;           // A, B, C, etc.
  fullTag: string;
}

export function parseISATag(tag: string): ISATagParts | null {
  const regex = /^([A-Z])([A-Z]*)-(\d+)([A-Z]?)$/;
  const match = tag.match(regex);
  
  if (!match) return null;
  
  return {
    measuredVariable: match[1],
    modifiers: match[2].split('').filter(Boolean),
    loopNumber: parseInt(match[3]),
    suffix: match[4] || undefined,
    fullTag: tag,
  };
}

/**
 * Generate ISA tag description
 */
export function getISATagDescription(tag: string): string {
  const parts = parseISATag(tag);
  if (!parts) return 'Unknown Tag';
  
  const variableNames: Record<string, string> = {
    F: 'Flow',
    P: 'Pressure',
    T: 'Temperature',
    L: 'Level',
    A: 'Analysis',
    S: 'Speed',
    W: 'Weight',
    V: 'Vibration',
  };
  
  const modifierNames: Record<string, string> = {
    I: 'Indicator',
    C: 'Controller',
    T: 'Transmitter',
    V: 'Valve',
    S: 'Switch',
    A: 'Alarm',
    R: 'Recorder',
    E: 'Element',
  };
  
  const variable = variableNames[parts.measuredVariable] || 'Unknown';
  const modifiers = parts.modifiers
    .map(m => modifierNames[m] || m)
    .join(' ');
  
  return modifiers ? `${variable} ${modifiers}` : variable;
}

/**
 * Generate default ISA tag for node type
 */
export function generateDefaultTag(type: string, index: number): string {
  const lowerType = type.toLowerCase();
  
  if (lowerType.includes('instrument')) {
    // Default to Flow Indicator Controller
    return `FIC-${100 + index}`;
  }
  if (lowerType.includes('valve')) {
    return `XV-${200 + index}`;
  }
  if (lowerType.includes('pump')) {
    return `P-${300 + index}`;
  }
  if (lowerType.includes('equipment')) {
    return `T-${400 + index}`;
  }
  return `MISC-${500 + index}`;
}

/**
 * Truncate label with ellipsis
 */
export function truncateLabel(label: string, maxLength: number = 15): string {
  if (label.length <= maxLength) return label;
  return label.substring(0, maxLength - 3) + '...';
}

/**
 * Get node style based on type and selection state
 */
export function getNodeStyle(
  type: string,
  isSelected: boolean = false,
  isFiltered: boolean = false
) {
  const color = getNodeColor(type);
  
  return {
    background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
    color: '#ffffff',
    border: `${isSelected ? 3 : 2}px solid ${color}`,
    borderRadius: `${NODE_DIMENSIONS.borderRadius}px`,
    padding: `${NODE_DIMENSIONS.padding}px`,
    minWidth: NODE_DIMENSIONS.minWidth,
    minHeight: NODE_DIMENSIONS.minHeight,
    boxShadow: isSelected
      ? `0 0 20px ${color}, 0 0 40px ${color}80`
      : `0 4px 6px ${color}40`,
    opacity: isFiltered ? 0.2 : 1,
    transition: 'all 0.2s ease-in-out',
    cursor: 'pointer',
  };
}
