import React, { useEffect, useState } from 'react';
import {
  FileText,
  Search,
  PlusCircle,
  Clock,
  ArrowRight,
  AlertCircle,
  Database,
  RefreshCw,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { api } from '../api/client';
import { NavTab } from '../components/layout/Sidebar';

interface CasesListProps {
  onSelectCase: (caseItem: any) => void;
  onNavigate: (tab: NavTab) => void;
}

export const CasesList: React.FC<CasesListProps> = ({ onSelectCase, onNavigate }) => {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState<string>('');

  const fetchCases = () => {
    setLoading(true);
    setError(null);
    api
      .listCases(50)
      .then((data) => {
        setCases(data || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch cases');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const filteredCases = cases.filter((c) => {
    const q = searchFilter.toLowerCase();
    const caseId = (c.case_id || '').toLowerCase();
    const symptoms = (Array.isArray(c.symptoms) ? c.symptoms.join(' ') : c.symptoms || '').toLowerCase();
    const history = (Array.isArray(c.history) ? c.history.join(' ') : c.history || '').toLowerCase();
    return caseId.includes(q) || symptoms.includes(q) || history.includes(q);
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-teal-700" />
            Patient Cases Directory
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Persisted cases in SQLite audit storage with structured lab panels and clinical histories.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="outline"
            leftIcon={<RefreshCw className="w-4 h-4 text-slate-500" />}
            onClick={fetchCases}
            isLoading={loading}
          >
            Refresh
          </Button>

          <Button
            size="sm"
            variant="primary"
            leftIcon={<PlusCircle className="w-4 h-4" />}
            onClick={() => onNavigate('new-case')}
          >
            New Clinical Case
          </Button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex items-center gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
        <Search className="w-4 h-4 text-slate-400 shrink-0 ml-1" />
        <input
          type="text"
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          placeholder="Filter by Case ID, reported symptom (e.g. fever, dyspnea), or comorbidity..."
          className="w-full text-xs text-slate-800 placeholder-slate-400 focus:outline-none bg-transparent"
        />
        {searchFilter && (
          <button
            onClick={() => setSearchFilter('')}
            className="text-xs text-slate-400 hover:text-slate-600 px-2"
          >
            Clear
          </button>
        )}
      </div>

      {/* Directory Table */}
      <Card bodyClassName="p-0">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            Fetching patient cases from database...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-600 space-y-2">
            <AlertCircle className="w-6 h-6 mx-auto" />
            <p>{error}</p>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-3">
            <Database className="w-8 h-8 mx-auto text-slate-300" />
            <p className="font-semibold text-slate-700">No matching patient cases found.</p>
            <p className="max-w-sm mx-auto">
              {searchFilter
                ? 'Try broadening your filter criteria.'
                : 'No cases have been created yet. Start a new case or load the demo case.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3 font-semibold">Case Identifier</th>
                  <th className="px-5 py-3 font-semibold">Demographics</th>
                  <th className="px-5 py-3 font-semibold">Reported Symptoms</th>
                  <th className="px-5 py-3 font-semibold">Attached Labs</th>
                  <th className="px-5 py-3 font-semibold">Created</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredCases.map((c) => (
                  <tr key={c.case_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-mono font-bold text-slate-900">
                      {c.case_id}
                    </td>
                    <td className="px-5 py-3.5 text-slate-600">
                      {c.age ? `${c.age}y` : 'Age N/A'}, {c.sex || 'Unknown'}
                    </td>
                    <td className="px-5 py-3.5 text-slate-700 max-w-xs truncate">
                      {Array.isArray(c.symptoms) ? c.symptoms.join(', ') : c.symptoms || '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {Array.isArray(c.labs) ? `${c.labs.length} tests` : '0 tests'}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 font-mono text-[11px]">
                      {c.created_at ? c.created_at.slice(0, 10) : 'Recent'}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                        onClick={() => {
                          onSelectCase(c);
                          onNavigate('new-case');
                        }}
                      >
                        Load Case
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
