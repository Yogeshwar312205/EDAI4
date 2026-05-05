/**
 * Component Palette - Draggable Equipment Library
 * 
 * Provides a sidebar with draggable P&ID components that can be added to the canvas
 */

import React, { useState } from 'react';
import { 
  Droplet, 
  Wind, 
  Gauge, 
  Box, 
  Circle, 
  Zap,
  ChevronLeft,
  ChevronRight,
  Layers
} from 'lucide-react';

interface ComponentItem {
  id: string;
  type: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}

const COMPONENT_LIBRARY: ComponentItem[] = [
  {
    id: 'valve',
    type: 'valve',
    label: 'Valve',
    icon: <Droplet className="w-5 h-5" />,
    color: '#56b6c2',
    description: 'Control or isolation valve'
  },
  {
    id: 'pump',
    type: 'pump',
    label: 'Pump',
    icon: <Wind className="w-5 h-5" />,
    color: '#e5c07b',
    description: 'Centrifugal or positive displacement pump'
  },
  {
    id: 'instrument',
    type: 'instrument',
    label: 'Instrument',
    icon: <Gauge className="w-5 h-5" />,
    color: '#61afef',
    description: 'Measurement or control instrument'
  },
  {
    id: 'tank',
    type: 'equipment',
    label: 'Tank',
    icon: <Box className="w-5 h-5" />,
    color: '#98c379',
    description: 'Storage tank or vessel'
  },
  {
    id: 'vessel',
    type: 'equipment',
    label: 'Vessel',
    icon: <Circle className="w-5 h-5" />,
    color: '#98c379',
    description: 'Pressure vessel or reactor'
  },
  {
    id: 'equipment',
    type: 'equipment',
    label: 'Equipment',
    icon: <Zap className="w-5 h-5" />,
    color: '#c678dd',
    description: 'Generic equipment'
  },
];

interface ComponentPaletteProps {
  isEditMode: boolean;
}

export const ComponentPalette: React.FC<ComponentPaletteProps> = ({ isEditMode }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const onDragStart = (event: React.DragEvent, componentType: string, componentLabel: string) => {
    event.dataTransfer.setData('application/reactflow', componentType);
    event.dataTransfer.setData('componentLabel', componentLabel);
    event.dataTransfer.effectAllowed = 'move';
  };

  if (!isEditMode) return null;

  return (
    <div className={`fixed left-4 top-24 z-40 transition-all duration-300 ${isCollapsed ? 'w-14' : 'w-72'}`}>
      {/* Collapse/Expand Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-4 bg-industrial-800 border border-industrial-600 rounded-full p-1.5 hover:bg-industrial-700 transition-colors shadow-lg z-50"
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-industrial-300" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-industrial-300" />
        )}
      </button>

      {/* Palette Container */}
      <div className="bg-industrial-800/95 backdrop-blur-md border border-industrial-600 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-accent-blue to-accent-cyan p-4 flex items-center gap-3">
          <Layers className="w-5 h-5 text-white" />
          {!isCollapsed && (
            <div>
              <h3 className="text-sm font-bold text-white">Component Library</h3>
              <p className="text-xs text-white/80">Drag to canvas</p>
            </div>
          )}
        </div>

        {/* Component List */}
        <div className="p-3 space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto">
          {COMPONENT_LIBRARY.map((component) => (
            <div
              key={component.id}
              draggable
              onDragStart={(e) => onDragStart(e, component.type, component.label)}
              className={`
                bg-industrial-900/50 border border-industrial-600 rounded-xl p-3
                hover:border-accent-blue hover:bg-industrial-700/50
                cursor-grab active:cursor-grabbing
                transition-all duration-200 hover:scale-105
                ${isCollapsed ? 'flex justify-center' : ''}
              `}
              title={isCollapsed ? component.label : ''}
            >
              <div className={`flex items-center gap-3 ${isCollapsed ? 'flex-col' : ''}`}>
                {/* Icon */}
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${component.color}20`, color: component.color }}
                >
                  {component.icon}
                </div>

                {/* Label & Description */}
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-industrial-100">
                      {component.label}
                    </h4>
                    <p className="text-xs text-industrial-400 truncate">
                      {component.description}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Instructions */}
        {!isCollapsed && (
          <div className="p-3 border-t border-industrial-600 bg-industrial-900/50">
            <div className="text-xs text-industrial-400 space-y-1">
              <p className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-blue" />
                Drag components to canvas
              </p>
              <p className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-cyan" />
                Connect nodes with handles
              </p>
              <p className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-green" />
                Delete: Select + Backspace
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComponentPalette;
