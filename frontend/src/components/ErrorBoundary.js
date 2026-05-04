import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          reset: this.handleReset,
        });
      }

      return (
        <div className="min-h-screen flex items-center justify-center px-4 py-8 bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-6 sm:p-8 text-center">
            <span className="text-5xl mb-4 block">⚠️</span>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Something Went Wrong
            </h2>
            <p className="text-gray-600 text-sm mb-6 leading-relaxed">
              An unexpected error occurred. This has been logged and we'll look into it.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 font-medium">
                  Technical details
                </summary>
                <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-red-700 overflow-auto max-h-40 whitespace-pre-wrap">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold rounded-lg transition-all shadow-md hover:shadow-lg text-sm"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all text-sm"
              >
                Reload Page
              </button>
              <button
                onClick={this.handleGoHome}
                className="px-5 py-2.5 text-indigo-600 hover:text-indigo-800 font-semibold text-sm"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
