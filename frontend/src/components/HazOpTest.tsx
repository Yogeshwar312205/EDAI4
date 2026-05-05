/**
 * Simple test component to verify HazOp tab is rendering
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const HazOpTest: React.FC = () => {
  console.log('HazOpTest component rendered!');
  
  return (
    <div className="w-full h-full flex items-center justify-center bg-industrial-800 rounded-lg border-2 border-accent-blue">
      <div className="text-center p-8">
        <AlertTriangle className="w-16 h-16 text-accent-blue mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-industrial-100 mb-2">
          HazOp Test Component
        </h2>
        <p className="text-industrial-400 mb-4">
          If you can see this, React is rendering correctly!
        </p>
        <div className="bg-industrial-900 p-4 rounded text-left text-sm font-mono">
          <p className="text-green-400">✓ Component mounted</p>
          <p className="text-green-400">✓ Styles applied</p>
          <p className="text-green-400">✓ Icons working</p>
        </div>
        <p className="text-yellow-400 mt-4 text-sm">
          Check browser console (F12) for debug messages
        </p>
      </div>
    </div>
  );
};

export default HazOpTest;
