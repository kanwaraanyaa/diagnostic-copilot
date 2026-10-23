import React, { useState } from 'react';
import {
  BookOpen,
  Search,
  ExternalLink,
  FileText,
  Database,
  Filter,
  CheckCircle2,
  Sparkles,
  Layers,
  Info,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Citation, DocumentType } from '../types/clinical';
import { api } from '../api/client';

interface EvidenceExplorerProps {
  activeCitations: Citation[];
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({ activeCitations }) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchResults, setSearchResults] = useState<Citation[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setSearchError(null);

    try {
      const results = await api.retrieveEvidence(searchQuery.trim(), 6);
      setSearchResults(results);
    } catch (err: any) {
      setSearchError(err.message || 'Corpus search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const getDocTypeBadge = (type: DocumentType | string) => {
    switch (type) {
      case 'clinical_guideline':
        return <Badge variant="teal">Clinical Guideline</Badge>;
      case 'peer_reviewed':
        return <Badge variant="info">Peer Reviewed</Badge>;
      case 'medical_database':
        return <Badge variant="neutral">Database Reference</Badge>;
      case 'educational':
        return <Badge variant="warning">Educational Corpus</Badge>;
      default:
        return <Badge variant="neutral">Medical Literature</Badge>;
    }
  };

  const displayedActive = filterType === 'all'
    ? activeCitations
    : activeCitations.filter((c) => c.document_type === filterType);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-teal-700" />
          Clinical Evidence Explorer & Knowledge Base
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Inspect ground-truth medical citations supporting diagnostic hypotheses and query the local knowledge base directly.
        </p>
      </div>

      {/* Interactive Search Tool */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-teal-700" />
            <span>Interactive Hybrid Knowledge Base Retrieval</span>
          </div>
        }
        subtitle="Dense vector embeddings (MiniLM-L6) + BM25 sparse index + lexical reranking"
      >
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. Community-acquired pneumonia CURB-65 criteria, troponin elevation in NSTEMI, CRP thresholds..."
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-100 focus:border-teal-600 transition-all bg-white"
            />
          </div>
          <Button
            type="submit"
            variant="primary"
            isLoading={isSearching}
            leftIcon={<Search className="w-4 h-4" />}
          >
            Search Corpus
          </Button>
        </form>

        {searchError && (
          <p className="text-xs text-rose-600 mt-2">{searchError}</p>
        )}

        {/* Live Search Results */}
        {searchResults && (
          <div className="mt-5 pt-4 border-t border-slate-100 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-semibold text-slate-700">
                Direct Retrieval Results ({searchResults.length} passages):
              </span>
              <button
                onClick={() => setSearchResults(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                Clear Results
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {searchResults.map((res, i) => (
                <div
                  key={i}
                  className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2 hover:border-teal-300 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-teal-900 truncate">
                      [{res.source_id}] {res.title}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                      Score: {(res.relevance_score || 0).toFixed(2)}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {getDocTypeBadge(res.document_type)}
                    <span className="text-[11px] text-slate-400 font-mono truncate">
                      {res.source.split(/[/\\]/).pop()}
                    </span>
                  </div>

                  <p className="text-slate-700 text-[11px] leading-relaxed bg-white p-2.5 rounded border border-slate-200/80">
                    "{res.content}"
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Active Case Citations */}
      <Card
        title={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-teal-700" />
              <span>Evidence Cited in Active Diagnostic Case</span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              {activeCitations.length} cited sources
            </span>
          </div>
        }
        subtitle="Verifiable medical literature referenced by the Specialist and Synthesizer agents"
        action={
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="text-xs bg-white border border-slate-300 rounded px-2 py-1 text-slate-700 focus:outline-none"
            >
              <option value="all">All Document Types</option>
              <option value="clinical_guideline">Clinical Guidelines</option>
              <option value="peer_reviewed">Peer Reviewed</option>
              <option value="educational">Educational</option>
            </select>
          </div>
        }
      >
        {activeCitations.length === 0 ? (
          <div className="p-10 text-center text-xs text-slate-400 space-y-2">
            <BookOpen className="w-8 h-8 mx-auto text-slate-300" />
            <p className="font-medium text-slate-600">No Case Evidence Loaded Yet</p>
            <p className="max-w-sm mx-auto text-slate-400">
              When a clinical case is analyzed, retrieved literature excerpts and source citations will appear here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {displayedActive.map((cit, idx) => (
              <div
                key={idx}
                className="p-4 bg-white rounded-xl border border-slate-200 text-xs space-y-3 shadow-2xs hover:shadow-xs transition-shadow"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-mono font-bold text-xs bg-teal-800 text-white px-2 py-0.5 rounded shrink-0">
                      [{cit.source_id}]
                    </span>
                    <h4 className="font-bold text-slate-900 truncate">{cit.title}</h4>
                  </div>
                  <span className="font-mono text-[11px] text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 shrink-0">
                    Relevance: {(cit.relevance_score || 0).toFixed(2)}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 border-y border-slate-100 py-1.5">
                  <div className="flex items-center gap-2">
                    {getDocTypeBadge(cit.document_type)}
                  </div>
                  <span className="font-mono text-slate-500 truncate max-w-xs">
                    File: {cit.source.split(/[/\\]/).pop()}
                  </span>
                </div>

                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/90 text-slate-700 text-[11px] leading-relaxed">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-1">
                    Verbatim Retrieved Excerpt:
                  </span>
                  "{cit.content}"
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
