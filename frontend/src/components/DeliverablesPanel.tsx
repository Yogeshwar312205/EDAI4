// Deliverables Panel - Generate Professional Excel Reports
import React, { useState } from 'react';
import { FileText, Loader2, CheckCircle, FileSpreadsheet } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

export const DeliverablesPanel: React.FC = () => {
  const [pidReference, setPidReference] = useState('P&ID-001');
  const [plcName, setPlcName] = useState('PLC-001');

  const generateMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append('pid_reference', pidReference);
      formData.append('plc_name', plcName);

      const response = await axios.post('/api/deliverables/generate', formData, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${pidReference}_deliverables.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      return response.data;
    },
  });

  return (
    <div className="h-full bg-industrial-900 rounded-lg border border-industrial-600 p-6 overflow-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-accent-green/20 rounded-lg flex items-center justify-center">
          <FileSpreadsheet className="w-6 h-6 text-accent-green" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-industrial-100">
            Generate Deliverables
          </h2>
          <p className="text-sm text-industrial-400">
            Professional Excel workbooks with Instrument Index, I/O List, and Alarm List
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-industrial-800 rounded-lg p-6 mb-6 border border-industrial-600">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-industrial-300 mb-2">
              P&ID Reference Number
            </label>
            <input
              type="text"
              value={pidReference}
              onChange={(e) => setPidReference(e.target.value)}
              placeholder="e.g., P&ID-001"
              className="w-full px-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 placeholder-industrial-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-industrial-300 mb-2">
              PLC/DCS Name
            </label>
            <input
              type="text"
              value={plcName}
              onChange={(e) => setPlcName(e.target.value)}
              placeholder="e.g., PLC-001"
              className="w-full px-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 placeholder-industrial-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
            />
          </div>

          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending || !pidReference}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-accent-green hover:bg-accent-green/80 disabled:bg-industrial-600 disabled:cursor-not-allowed text-industrial-950 font-semibold rounded-lg transition-all shadow-glow-cyan"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : generateMutation.isSuccess ? (
              <>
                <CheckCircle className="w-5 h-5" />
                Generated Successfully!
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                Generate Excel Deliverables
              </>
            )}
          </button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <InfoCard
          icon={<FileText className="w-5 h-5" />}
          title="Instrument Index"
          description="Complete catalog of all instruments with tags, types, and locations"
          color="blue"
        />
        <InfoCard
          icon={<FileText className="w-5 h-5" />}
          title="I/O List"
          description="Auto-categorized AI, AO, DI, DO signals with PLC assignments"
          color="cyan"
        />
        <InfoCard
          icon={<FileText className="w-5 h-5" />}
          title="Alarm List"
          description="Safety-critical alarms and trips with priorities"
          color="yellow"
        />
      </div>

      {/* Features List */}
      <div className="bg-industrial-800 rounded-lg p-6 border border-industrial-600">
        <h3 className="text-lg font-semibold text-industrial-200 mb-4">
          What's Included
        </h3>
        <div className="space-y-3">
          <Feature text="Professional formatting with color-coded headers" />
          <Feature text="ISA S5.1 compliant tag parsing and validation" />
          <Feature text="Automatic I/O signal type classification" />
          <Feature text="Alarm priority categorization (Critical/High/Medium)" />
          <Feature text="Auto-adjusted column widths and frozen headers" />
          <Feature text="Client-ready Excel format (.xlsx)" />
        </div>
      </div>

      {/* Error Display */}
      {generateMutation.isError && (
        <div className="mt-4 p-4 bg-accent-red/20 border border-accent-red rounded-lg">
          <p className="text-accent-red text-sm">
            Error: {(generateMutation.error as Error).message}
          </p>
        </div>
      )}
    </div>
  );
};

const InfoCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  color: 'blue' | 'cyan' | 'yellow';
}> = ({ icon, title, description, color }) => {
  const colors = {
    blue: 'bg-accent-blue/20 text-accent-blue border-accent-blue/30',
    cyan: 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30',
    yellow: 'bg-accent-yellow/20 text-accent-yellow border-accent-yellow/30',
  };

  return (
    <div className={`p-4 rounded-lg border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <h4 className="font-semibold">{title}</h4>
      </div>
      <p className="text-xs text-industrial-400">{description}</p>
    </div>
  );
};

const Feature: React.FC<{ text: string }> = ({ text }) => (
  <div className="flex items-start gap-2">
    <CheckCircle className="w-4 h-4 text-accent-green mt-0.5 flex-shrink-0" />
    <span className="text-sm text-industrial-300">{text}</span>
  </div>
);
