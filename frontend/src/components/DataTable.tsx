// Feature 2: Cross-Linked Data Table with Canvas Sync
import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import { useAppStore } from '@/store/useAppStore';
import type { DetectionResult } from '@/types/api';
import { ArrowUpDown, Search } from 'lucide-react';

interface DataTableProps {
  detections: DetectionResult[];
}

type TableRow = DetectionResult & { id: string; index: number };

const columnHelper = createColumnHelper<TableRow>();

export const DataTable: React.FC<DataTableProps> = ({ detections }) => {
  const { selectedNodeId, setSelectedNodeId, setActiveView } = useAppStore();
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = React.useState('');

  // Transform detections to table rows
  const data = useMemo<TableRow[]>(
    () =>
      detections.map((detection, index) => ({
        ...detection,
        id: `node_${index}`,
        index,
      })),
    [detections]
  );

  // Define columns
  const columns = useMemo(
    () => [
      columnHelper.accessor('index', {
        header: '#',
        cell: (info) => (
          <span className="text-industrial-400 font-mono text-sm">
            {info.getValue() + 1}
          </span>
        ),
        size: 50,
      }),
      columnHelper.accessor('tag', {
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting()}
            className="flex items-center gap-2 hover:text-accent-blue transition-colors"
          >
            Tag
            <ArrowUpDown className="w-4 h-4" />
          </button>
        ),
        cell: (info) => {
          const tag = info.getValue();
          return (
            <span className="font-mono font-bold text-accent-cyan">
              {tag || <span className="text-industrial-500 italic">N/A</span>}
            </span>
          );
        },
        size: 120,
      }),
      columnHelper.accessor('class_name', {
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting()}
            className="flex items-center gap-2 hover:text-accent-blue transition-colors"
          >
            Class
            <ArrowUpDown className="w-4 h-4" />
          </button>
        ),
        cell: (info) => {
          const className = info.getValue();
          const color = getClassColor(className);
          return (
            <span
              className="px-2 py-1 rounded text-xs font-medium"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {className}
            </span>
          );
        },
        size: 180,
      }),
      columnHelper.accessor('confidence', {
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting()}
            className="flex items-center gap-2 hover:text-accent-blue transition-colors"
          >
            Confidence
            <ArrowUpDown className="w-4 h-4" />
          </button>
        ),
        cell: (info) => {
          const confidence = info.getValue();
          const percentage = (confidence * 100).toFixed(1);
          const color =
            confidence > 0.8
              ? '#98c379'
              : confidence > 0.5
              ? '#e5c07b'
              : '#e06c75';
          return (
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-industrial-700 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
              <span className="text-sm font-mono" style={{ color }}>
                {percentage}%
              </span>
            </div>
          );
        },
        size: 150,
      }),
      columnHelper.display({
        id: 'location',
        header: 'Location',
        cell: (info) => {
          const detection = info.row.original;
          // Convert percentage to display format (0-100%)
          const x = (detection.pct_x * 100).toFixed(1);
          const y = (detection.pct_y * 100).toFixed(1);
          return (
            <span className="text-xs font-mono text-industrial-400">
              ({x}%, {y}%)
            </span>
          );
        },
        size: 100,
      }),
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  // Handle row click - zoom canvas to detection
  const handleRowClick = (rowId: string) => {
    setSelectedNodeId(rowId);
    setActiveView('canvas'); // Switch to canvas view
  };

  const getClassColor = (className: string): string => {
    if (className.includes('instrument')) return '#61afef';
    if (className.includes('valve')) return '#56b6c2';
    if (className.includes('equipment')) return '#98c379';
    if (className.includes('pump')) return '#e5c07b';
    return '#c678dd';
  };

  return (
    <div 
      className="flex flex-col h-full bg-industrial-800 rounded-lg border border-industrial-600"
      onWheel={(e) => {
        // Prevent scroll propagation to canvas
        e.stopPropagation();
      }}
    >
      {/* Header with Search */}
      <div className="p-4 border-b border-industrial-600">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-industrial-400" />
            <input
              type="text"
              value={globalFilter ?? ''}
              onChange={(e) => setGlobalFilter(e.target.value)}
              placeholder="Search tags, classes..."
              className="w-full pl-10 pr-4 py-2 bg-industrial-900 border border-industrial-600 rounded-lg text-industrial-200 placeholder-industrial-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue transition-colors"
            />
          </div>
          <div className="text-sm text-industrial-400 font-mono">
            {table.getFilteredRowModel().rows.length} / {data.length} items
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-industrial-700 z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-sm font-semibold text-industrial-200 border-b border-industrial-600"
                    style={{ width: header.getSize() }}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => {
              const isSelected = selectedNodeId === row.original.id;
              return (
                <tr
                  key={row.id}
                  onClick={() => handleRowClick(row.original.id)}
                  className={`
                    cursor-pointer transition-all
                    hover:bg-industrial-700/50
                    ${
                      isSelected
                        ? 'bg-accent-blue/20 border-l-4 border-accent-blue'
                        : 'border-l-4 border-transparent'
                    }
                  `}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-4 py-3 text-sm text-industrial-300 border-b border-industrial-700/50"
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Stats */}
      <div className="p-3 border-t border-industrial-600 bg-industrial-900/50">
        <div className="flex gap-4 text-xs text-industrial-400 font-mono">
          <div>
            Instruments:{' '}
            <span className="text-accent-cyan font-bold">
              {data.filter((d) => d.class_name.includes('instrument')).length}
            </span>
          </div>
          <div>
            Valves:{' '}
            <span className="text-accent-blue font-bold">
              {data.filter((d) => d.class_name.includes('valve')).length}
            </span>
          </div>
          <div>
            Equipment:{' '}
            <span className="text-accent-green font-bold">
              {data.filter((d) => d.class_name.includes('equipment')).length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
