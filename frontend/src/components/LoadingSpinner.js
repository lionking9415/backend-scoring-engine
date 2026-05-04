import React from 'react';

const sizes = {
  sm: 'h-6 w-6 border-2',
  md: 'h-12 w-12 border-3',
  lg: 'h-16 w-16 border-4',
};

const Spinner = ({ size = 'md', className = '' }) => (
  <div
    className={`animate-spin rounded-full border-indigo-600 border-t-transparent ${sizes[size] || sizes.md} ${className}`}
    role="status"
    aria-label="Loading"
  />
);

const LoadingSpinner = ({
  size = 'lg',
  message = 'Loading...',
  submessage,
  variant = 'fullscreen',
  className = '',
}) => {
  if (variant === 'inline') {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        <Spinner size="sm" />
        {message && <span className="text-sm text-gray-600">{message}</span>}
      </div>
    );
  }

  if (variant === 'overlay') {
    return (
      <div className={`fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm ${className}`}>
        <div className="text-center">
          <Spinner size={size} className="mx-auto mb-4" />
          {message && <p className="text-gray-700 font-medium">{message}</p>}
          {submessage && <p className="text-xs text-gray-400 mt-2">{submessage}</p>}
        </div>
      </div>
    );
  }

  // fullscreen (default)
  return (
    <div className={`min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4 ${className}`}>
      <div className="text-center">
        <Spinner size={size} className="mx-auto mb-4" />
        {message && <p className="text-gray-700 font-medium">{message}</p>}
        {submessage && <p className="text-xs text-gray-400 mt-2">{submessage}</p>}
      </div>
    </div>
  );
};

const SkeletonLine = ({ width = 'w-full', className = '' }) => (
  <div className={`h-3 bg-gray-200 rounded animate-pulse ${width} ${className}`} />
);

const SkeletonCard = ({ lines = 3, className = '' }) => (
  <div className={`bg-white rounded-xl border border-gray-200 p-5 space-y-3 animate-pulse ${className}`}>
    <div className="h-4 bg-gray-200 rounded w-2/5" />
    {Array.from({ length: lines }).map((_, i) => (
      <SkeletonLine key={i} width={i === lines - 1 ? 'w-3/5' : i % 2 === 0 ? 'w-full' : 'w-5/6'} />
    ))}
  </div>
);

const ErrorAlert = ({
  error,
  onDismiss,
  onRetry,
  className = '',
}) => {
  if (!error) return null;
  const message = typeof error === 'string'
    ? error
    : error?.message || 'An unexpected error occurred.';

  return (
    <div className={`p-4 bg-red-50 border border-red-200 rounded-xl ${className}`} role="alert">
      <div className="flex items-start gap-3">
        <span className="text-red-500 text-lg shrink-0">⚠️</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-red-800 leading-relaxed">{message}</p>
          <div className="flex items-center gap-3 mt-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
              >
                Try again
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-gray-400 hover:text-gray-600 text-lg leading-none shrink-0"
            aria-label="Dismiss"
          >
            &times;
          </button>
        )}
      </div>
    </div>
  );
};

export default LoadingSpinner;
export { Spinner, SkeletonCard, SkeletonLine, ErrorAlert };
