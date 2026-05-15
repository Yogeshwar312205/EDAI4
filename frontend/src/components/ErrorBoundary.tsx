import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-industrial-950 flex items-center justify-center p-6">
          <div className="max-w-2xl w-full bg-industrial-800 rounded-lg border-2 border-accent-red p-8">
            <div className="flex items-center gap-4 mb-6">
              <AlertTriangle className="w-12 h-12 text-accent-red" />
              <div>
                <h1 className="text-2xl font-bold text-industrial-100">
                  Something Went Wrong
                </h1>
                <p className="text-industrial-400">
                  The application encountered an error
                </p>
              </div>
            </div>

            <div className="bg-industrial-900 rounded p-4 mb-4">
              <h2 className="text-sm font-bold text-accent-red mb-2">Error:</h2>
              <pre className="text-xs text-industrial-300 overflow-auto">
                {this.state.error?.toString()}
              </pre>
            </div>

            {this.state.errorInfo && (
              <div className="bg-industrial-900 rounded p-4 mb-4">
                <h2 className="text-sm font-bold text-accent-red mb-2">
                  Component Stack:
                </h2>
                <pre className="text-xs text-industrial-300 overflow-auto max-h-64">
                  {this.state.errorInfo.componentStack}
                </pre>
              </div>
            )}

            <button
              onClick={() => window.location.reload()}
              className="w-full px-4 py-2 bg-accent-blue text-white rounded hover:bg-accent-cyan transition-colors"
            >
              Reload Page
            </button>

            <div className="mt-4 text-xs text-industrial-500">
              <p>Please check the browser console (F12) for more details.</p>
              <p className="mt-2">
                If this persists, please report this error with the details above.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
