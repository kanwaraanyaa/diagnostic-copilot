import React from 'react';
import {
  Activity,
  FileText,
  PlusCircle,
  ImageIcon,
  GitBranch,
  BookOpen,
  ClipboardList,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  FlaskConical,
} from 'lucide-react';
import { HealthResponse } from '../../types/clinical';

export type NavTab =
  | 'overview'
  | 'cases'
  | 'new-case'
  | 'imaging'
  | 'workflow'
  | 'evidence'
  | 'reports'
  | 'evaluation'
  | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  hasActiveReport: boolean;
  hasActiveImage: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  health,
  healthLoading,
  hasActiveReport,
  hasActiveImage,
}) => {
  const navItems = [
    {
      id: 'overview' as NavTab,
      label: 'Clinical Overview',
      icon: Activity,
      badge: null,
    },
    {
      id: 'cases' as NavTab,
      label: 'Patient Cases',
      icon: FileText,
      badge: null,
    },
    {
      id: 'new-case' as NavTab,
      label: 'New Clinical Analysis',
      icon: PlusCircle,
      badge: null,
    },
    {
      id: 'imaging' as NavTab,
      label: 'Imaging Workspace',
      icon: ImageIcon,
      badge: hasActiveImage ? '1 active' : null,
    },
    {
      id: 'workflow' as NavTab,
      label: 'AI Multi-Agent Trace',
      icon: GitBranch,
      badge: null,
    },
    {
      id: 'evidence' as NavTab,
      label: 'Evidence Library',
      icon: BookOpen,
      badge: null,
    },
    {
      id: 'reports' as NavTab,
      label: 'Clinical Reports',
      icon: ClipboardList,
      badge: hasActiveReport ? 'Ready' : null,
    },
    {
      id: 'evaluation' as NavTab,
      label: 'Research & Evaluation',
      icon: FlaskConical,
      badge: null,
    },
    {
      id: 'settings' as NavTab,
      label: 'System Settings',
      icon: Settings,
      badge: null,
    },
  ];

  return (
    <aside
      className={`no-print flex flex-col bg-slate-900 text-slate-200 border-r border-slate-800 transition-all duration-300 relative select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800 bg-slate-950/40">
        <div className="flex items-center overflow-hidden flex-1 mr-2">
          {!collapsed ? (
            <div className="bg-white/95 hover:bg-white rounded-lg px-2.5 py-1.5 flex items-center shadow-xs border border-slate-700/40 transition-all max-w-[190px]">
              <img
                src="/medorchestr_logo.png"
                alt="MedOrchestr AI"
                className="h-7 w-auto object-contain select-none"
              />
            </div>
          ) : (
            <div className="bg-white/95 rounded-lg p-1.5 flex items-center justify-center shadow-xs border border-slate-700/40" title="MedOrchestr AI">
              <img
                src="/medorchestr_icon.png"
                alt="MedOrchestr AI"
                className="w-5 h-7 object-contain select-none"
              />
            </div>
          )}
        </div>
        <button
          onClick={onToggleCollapse}
          className="text-slate-400 hover:text-white p-1.5 rounded-md hover:bg-slate-800/80 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-teal-600/20 text-teal-300 border border-teal-500/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white border border-transparent'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={`w-4 h-4 shrink-0 ${
                  isActive ? 'text-teal-400' : 'text-slate-400'
                }`}
              />
              {!collapsed && (
                <span className="truncate flex-1 text-left">{item.label}</span>
              )}
              {!collapsed && item.badge && (
                <span className="text-[10px] font-semibold bg-teal-900/60 text-teal-300 px-1.5 py-0.5 rounded border border-teal-700/50">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Mandatory Safety Notice */}
      {!collapsed && (
        <div className="p-3 bg-slate-950/70 border-t border-slate-800 text-[10px] text-slate-400 leading-relaxed">
          <div className="flex items-start gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <span>
              For research and educational use only. Does not replace clinical evaluation by a qualified medical professional.
            </span>
          </div>
        </div>
      )}
    </aside>
  );
};
