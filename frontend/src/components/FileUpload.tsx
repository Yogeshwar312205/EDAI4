// File Upload Component with Drag & Drop
import React, { useCallback, useState } from 'react';
import { Upload, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { edaiAPI } from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';

export const FileUpload: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const { setUploadedImage, setProcessingResult, setGraphData } = useAppStore();

  const uploadMutation = useMutation({
    mutationFn: edaiAPI.processImage,
    onSuccess: async (data) => {
      setProcessingResult(data);
      
      // Fetch graph data with error handling
      try {
        const graphData = await edaiAPI.getGraph();
        
        // Validate graph data before setting
        if (graphData && graphData.nodes && Array.isArray(graphData.nodes)) {
          setGraphData(graphData);
          console.log('Graph data loaded:', graphData.nodes.length, 'nodes');
        } else {
          console.warn('Invalid graph data received:', graphData);
          setGraphData(null);
        }
      } catch (error) {
        console.error('Failed to fetch graph:', error);
        // Don't fail the whole upload if graph fetch fails
        setGraphData(null);
      }
    },
    onError: (error) => {
      console.error('Upload failed:', error);
    },
  });

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith('image/')) {
        alert('Please upload an image file');
        return;
      }

      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      // Upload to backend
      uploadMutation.mutate(file);
    },
    [uploadMutation, setUploadedImage]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const onFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="w-full">
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center transition-all
          ${
            isDragging
              ? 'border-accent-blue bg-accent-blue/10 scale-105'
              : 'border-industrial-600 hover:border-industrial-500'
          }
          ${uploadMutation.isPending ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept="image/*"
          onChange={onFileSelect}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-4">
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="w-16 h-16 text-accent-blue animate-spin" />
              <div className="space-y-2">
                <p className="text-lg font-semibold text-industrial-200">
                  Processing P&ID...
                </p>
                <p className="text-sm text-industrial-400">
                  Running YOLO detection, OCR, and graph analysis
                </p>
              </div>
            </>
          ) : uploadMutation.isSuccess ? (
            <>
              <CheckCircle className="w-16 h-16 text-accent-green" />
              <div className="space-y-2">
                <p className="text-lg font-semibold text-accent-green">
                  Processing Complete!
                </p>
                <p className="text-sm text-industrial-400">
                  Processed in {uploadMutation.data.processing_time_ms.toFixed(0)}ms
                </p>
              </div>
            </>
          ) : uploadMutation.isError ? (
            <>
              <XCircle className="w-16 h-16 text-accent-red" />
              <div className="space-y-2">
                <p className="text-lg font-semibold text-accent-red">
                  Processing Failed
                </p>
                <p className="text-sm text-industrial-400">
                  {(uploadMutation.error as Error).message}
                </p>
              </div>
            </>
          ) : (
            <>
              <Upload className="w-16 h-16 text-industrial-400" />
              <div className="space-y-2">
                <p className="text-lg font-semibold text-industrial-200">
                  Upload P&ID Image
                </p>
                <p className="text-sm text-industrial-400">
                  Drag & drop or click to browse
                </p>
                <p className="text-xs text-industrial-500 font-mono">
                  Supports: JPG, PNG, TIFF
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Processing Stats */}
      {uploadMutation.isSuccess && uploadMutation.data && (
        <div className="mt-4 grid grid-cols-4 gap-4">
          <StatCard
            label="Symbols"
            value={uploadMutation.data.layer1_detections}
            color="blue"
          />
          <StatCard
            label="Instruments"
            value={uploadMutation.data.layer2_instruments}
            color="cyan"
          />
          <StatCard
            label="Nodes"
            value={uploadMutation.data.layer3_nodes}
            color="green"
          />
          <StatCard
            label="Edges"
            value={uploadMutation.data.layer3_edges}
            color="yellow"
          />
        </div>
      )}
    </div>
  );
};

const StatCard: React.FC<{
  label: string;
  value: number;
  color: 'blue' | 'cyan' | 'green' | 'yellow';
}> = ({ label, value, color }) => {
  const colors = {
    blue: 'text-accent-blue',
    cyan: 'text-accent-cyan',
    green: 'text-accent-green',
    yellow: 'text-accent-yellow',
  };

  return (
    <div className="bg-industrial-800 rounded-lg p-4 border border-industrial-600">
      <div className={`text-3xl font-bold font-mono ${colors[color]}`}>
        {value}
      </div>
      <div className="text-sm text-industrial-400 mt-1">{label}</div>
    </div>
  );
};
