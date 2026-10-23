import React from 'react';
import { UncertaintyLevel } from '../../types/clinical';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'teal';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
}) => {
  const variantStyles = {
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border-amber-200',
    danger: 'bg-rose-50 text-rose-800 border-rose-200',
    info: 'bg-sky-50 text-sky-800 border-sky-200',
    teal: 'bg-teal-50 text-teal-800 border-teal-200',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};

export const UncertaintyBadge: React.FC<{ level: UncertaintyLevel | string; showLabel?: boolean }> = ({
  level,
  showLabel = true,
}) => {
  const normalized = (level || 'unknown').toLowerCase() as UncertaintyLevel;

  switch (normalized) {
    case 'low':
      return (
        <Badge variant="success">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          {showLabel ? 'Low Uncertainty' : 'Low'}
        </Badge>
      );
    case 'moderate':
      return (
        <Badge variant="warning">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          {showLabel ? 'Moderate Uncertainty' : 'Moderate'}
        </Badge>
      );
    case 'high':
      return (
        <Badge variant="danger">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
          {showLabel ? 'High Uncertainty' : 'High'}
        </Badge>
      );
    default:
      return (
        <Badge variant="neutral">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          {showLabel ? 'Unspecified Uncertainty' : 'Unknown'}
        </Badge>
      );
  }
};
