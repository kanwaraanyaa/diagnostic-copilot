import React from 'react';
import { User, FileText, ImageIcon, RefreshCw, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { PatientCase } from '../../types/clinical';

interface HeaderProps {
  title: string;
  subtitle?: string;
  currentCase: Partial<PatientCase>;
  onLoadDemo: () => void;
  onReset: () => void;
  isDemoLoaded: boolean;
  onNavigateToReport?: () => void;
  hasActiveReport: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  currentCase,
  onLoadDemo,
  onReset,
  isDemoLoaded,
  onNavigateToReport,
  hasActiveReport,
}) => {
  const hasPatientData = Boolean(
    currentCase.patient_id || currentCase.age || (currentCase.symptoms && currentCase.symptoms.length > 0)
  );

  return (
    <header className="no-print h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-xs z-10">
      {/* Title & Subtitle */}
      <div className="flex flex-col">
        <h1 className="text-base font-semibold text-slate-900 tracking-tight flex items-center gap-2">
          {title}
        </h1>
        {subtitle && <p className="text-xs text-slate-500 font-normal">{subtitle}</p>}
      </div>

      {/* Patient Identity Strip & Global Actions */}
      <div className="flex items-center gap-3">
        {hasPatientData && (
          <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs">
            <User className="w-3.5 h-3.5 text-teal-600" />
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800 font-mono">
                {currentCase.patient_id || 'PT-UNASSIGNED'}
              </span>
              <span className="text-slate-300">|</span>
              <span className="text-slate-600">
                {currentCase.age ? `${currentCase.age}y` : 'Age N/A'}, {currentCase.sex || 'Unknown'}
              </span>
              {currentCase.image_path && (
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
                  <ImageIcon className="w-3 h-3" /> CXR Attached
                </span>
              )}
              {isDemoLoaded && (
                <span className="text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded">
                  Synthetic Demo
                </span>
              )}
            </div>
          </div>
        )}

        {hasActiveReport && onNavigateToReport && (
          <Button
            size="sm"
            variant="outline"
            leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
            onClick={onNavigateToReport}
            className="border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
          >
            Report Ready
          </Button>
        )}

        <Button
          size="sm"
          variant="outline"
          leftIcon={<Sparkles className="w-3.5 h-3.5 text-teal-600" />}
          onClick={onLoadDemo}
        >
          {isDemoLoaded ? 'Reload Demo Case' : 'Load Demo Case & CXR'}
        </Button>

        <Button
          size="sm"
          variant="ghost"
          leftIcon={<RefreshCw className="w-3.5 h-3.5 text-slate-400" />}
          onClick={onReset}
          title="Clear active patient case"
        >
          Reset
        </Button>
      </div>
    </header>
  );
};
