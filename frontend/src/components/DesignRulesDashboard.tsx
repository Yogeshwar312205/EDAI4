// Design Rules Dashboard - Automated Quality Control
import React, { useEffect, useState } from 'react';
import { Shield, AlertCircle, AlertTriangle, Info, Filter, Download } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAppStore } from '@/store/useAppStore';

interface RuleViolation {
  rule_id: string;
  rule_name: string;
  severity: 'Critical' | 'Warning' | 'Info';
  description: string;
  affected_items: string[];
  recommendation: string;
  location?: { x: number; y: number };
}

export const DesignRulesDashboard: React.FC = () => {
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const { setSelectedNodeId, setActiveView } = useAppStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ['design-rules'],
    queryFn: async () => {
      const response = await axios.get('/api/design-rules/check');
      return response.data;
    },
    refetchInterval: false,
  });

  const violations: RuleViolation[] = data?.violations || [];
  const filteredViolations = violations.filter(
    (v) => filterSeverity === 'all' || v.severity === filterSeverity
  );

  const handleViewViolation = (violation: RuleViolation) => {
    if (violation.location) {
      // Find node at this location and zoom to it
      // This would require mapping location to node ID
      setActiveView('canvas');
    }
  };

  return (
    <div className="h-full bg-industrial-900 rounded-lg border border-industrial-600 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-industrial-600">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-accent-blue/20 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-accent-blue" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-industrial-100">
                Design Rule Checker
              </h2>
              <p className="text-sm text-industrial-400">
                Automated quality control and standards compliance
              </p>
            </div>
          </div>
          <button
            onClick={() => {/* Export report */}}
            className="flex items-center gap-2 px-4 py-2 bg-industrial-700 hover:bg-industrial-600 text-industrial-200 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>

        {/* Summary Cards */}
        {!isLoading && data && (
          <div className="grid grid-cols-4 gap-4">
            <SummaryCard
              label="Total Violations"
              value={data.total_violations}
              color="gray"
              icon={<Shield className="w-5 h-5" />}
            />
            <SummaryCard
              label="Critical"
              value={data.critical}
              color="red"
              icon={<AlertCircle className="w-5 h-5" />}
            />
            <SummaryCard
              label="Warnings"
              value={data.warnings}
              color="yellow"
              icon={<AlertTriangle className="w-5 h-5" />}
            />
            <SummaryCard
              label="Info"
              value={data.info}
              color="blue"
              icon={<Info className="w-5 h-5" />}
            />
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="p-4 border-b border-industrial-600 bg-industrial-800">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-industrial-400" />
          <span className="text-sm text-industrial-400 mr-2">Filter:</span>
          <FilterButton
            label="All"
            active={filterSeverity === 'all'}
            onClick={() => setFilterSeverity('all')}
            count={violations.length}
          />
          <FilterButton
            label="Critical"
            active={filterSeverity === 'Critical'}
            onClick={() => setFilterSeverity('Critical')}
            count={data?.critical || 0}
            color="red"
          />
          <FilterButton
            label="Warning"
            active={filterSeverity === 'Warning'}
            onClick={() => setFilterSeverity('Warning')}
            count={data?.warnings || 0}
            color="yellow"
          />
          <FilterButton
            label="Info"
            active={filterSeverity === 'Info'}
            onClick={() => setFilterSeverity('Info')}
            count={data?.info || 0}
            color="blue"
          />
        </div>
      </div>

      {/* Violations List */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-industrial-400">Checking design rules...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-accent-red mx-auto mb-4" />
              <p className="text-industrial-400">
                Error loading design rules. Process a P&ID first.
              </p>
            </div>
          </div>
        ) : filteredViolations.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Shield className="w-12 h-12 text-accent-green mx-auto mb-4" />
              <p className="text-industrial-200 font-semibold mb-2">
                No violations found!
              </p>
              <p className="text-industrial-400 text-sm">
                Your P&ID meets all design rule requirements.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredViolations.map((violation, index) => (
              <ViolationCard
                key={index}
                violation={violation}
                onView={() => handleViewViolation(violation)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const SummaryCard: React.FC<{
  label: string;
  value: number;
  color: 'gray' | 'red' | 'yellow' | 'blue';
  icon: React.ReactNode;
}> = ({ label, value, color, icon }) => {
  const colors = {
    gray: 'bg-industrial-700 text-industrial-300',
    red: 'bg-accent-red/20 text-accent-red',
    yellow: 'bg-accent-yellow/20 text-accent-yellow',
    blue: 'bg-accent-blue/20 text-accent-blue',
  };

  return (
    <div className={`p-4 rounded-lg ${colors[color]}`}>
      <div className="flex items-center justify-between mb-2">
        {icon}
        <span className="text-2xl font-bold">{value}</span>
      </div>
      <p className="text-xs opacity-80">{label}</p>
    </div>
  );
};

const FilterButton: React.FC<{
  label: string;
  active: boolean;
  onClick: () => void;
  count: number;
  color?: 'red' | 'yellow' | 'blue';
}> = ({ label, active, onClick, count, color }) => {
  const colors = {
    red: 'bg-accent-red/20 text-accent-red border-accent-red',
    yellow: 'bg-accent-yellow/20 text-accent-yellow border-accent-yellow',
    blue: 'bg-accent-blue/20 text-accent-blue border-accent-blue',
  };

  const activeClass = active
    ? color
      ? colors[color]
      : 'bg-accent-blue/20 text-accent-blue border-accent-blue'
    : 'bg-industrial-700 text-industrial-300 border-industrial-600';

  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-all ${activeClass}`}
    >
      {label} ({count})
    </button>
  );
};

const ViolationCard: React.FC<{
  violation: RuleViolation;
  onView: () => void;
}> = ({ violation, onView }) => {
  const severityConfig = {
    Critical: {
      icon: <AlertCircle className="w-5 h-5" />,
      color: 'border-accent-red bg-accent-red/10',
      badge: 'bg-accent-red text-industrial-950',
    },
    Warning: {
      icon: <AlertTriangle className="w-5 h-5" />,
      color: 'border-accent-yellow bg-accent-yellow/10',
      badge: 'bg-accent-yellow text-industrial-950',
    },
    Info: {
      icon: <Info className="w-5 h-5" />,
      color: 'border-accent-blue bg-accent-blue/10',
      badge: 'bg-accent-blue text-industrial-950',
    },
  };

  const config = severityConfig[violation.severity];

  return (
    <div
      className={`p-4 rounded-lg border-l-4 ${config.color} transition-all hover:shadow-lg`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5">{config.icon}</div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${config.badge}`}>
                {violation.severity}
              </span>
              <span className="text-xs text-industrial-500 font-mono">
                {violation.rule_id}
              </span>
            </div>
            <h4 className="font-semibold text-industrial-200 mb-1">
              {violation.rule_name}
            </h4>
            <p className="text-sm text-industrial-400 mb-2">
              {violation.description}
            </p>
          </div>
        </div>
      </div>

      {/* Affected Items */}
      {violation.affected_items.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-industrial-500 mb-1">Affected Items:</p>
          <div className="flex flex-wrap gap-1">
            {violation.affected_items.map((item, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-industrial-700 text-industrial-300 rounded text-xs font-mono"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommendation */}
      <div className="mb-3 p-3 bg-industrial-800 rounded">
        <p className="text-xs text-industrial-500 mb-1">Recommendation:</p>
        <p className="text-sm text-industrial-300">{violation.recommendation}</p>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={onView}
          className="px-3 py-1.5 bg-accent-blue hover:bg-accent-blue/80 text-industrial-950 text-sm font-medium rounded transition-colors"
        >
          View on Canvas
        </button>
      </div>
    </div>
  );
};
