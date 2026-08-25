import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { QueryInput } from './components/QueryInput';
import { SuggestionCard } from './components/SuggestionCard';
import { DynamicPlaceholderForm } from './components/DynamicPlaceholderForm';
import { ResultTable } from './components/ResultTable';
import { DeveloperStudio } from './components/DeveloperStudio';
import { TemplateSuggestion, QueryExecutionResult } from './types';
import { fetchHealthStatus, fetchSuggestions, executeQueryTemplate } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'query' | 'developer'>('query');
  const [health, setHealth] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<TemplateSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<TemplateSuggestion | null>(null);
  const [executionResult, setExecutionResult] = useState<QueryExecutionResult | null>(null);
  
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Poll backend health status on mount
  useEffect(() => {
    fetchHealthStatus().then((data) => setHealth(data));
  }, []);

  const handleSearch = async (queryText: string) => {
    setLoadingSuggestions(true);
    setErrorMsg(null);
    setSelectedSuggestion(null);
    setExecutionResult(null);

    try {
      const response = await fetchSuggestions(queryText);
      setSuggestions(response.suggestions);
      if (response.suggestions.length > 0) {
        setSelectedSuggestion(response.suggestions[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch template suggestions.');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleExecute = async (parameters: Record<string, any>) => {
    if (!selectedSuggestion) return;
    setExecuting(true);
    setErrorMsg(null);

    try {
      const result = await executeQueryTemplate(selectedSuggestion.template_id, parameters);
      setExecutionResult(result);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to execute query template.');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="app-container">
      <Header
        health={health}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
      />

      <main>
        {activeTab === 'developer' ? (
          <DeveloperStudio />
        ) : (
          <>
            <QueryInput onSearch={handleSearch} loading={loadingSuggestions} />

            {errorMsg && (
              <div className="glass-panel" style={{ borderColor: 'rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.05)', color: '#f87171' }}>
                ⚠️ {errorMsg}
              </div>
            )}

            {suggestions.length > 0 && (
              <div className="glass-panel">
                <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>
                  Top Matching Approved Query Templates
                </h2>
                <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                  Select a template to view detected entity values or resolve missing placeholders.
                </p>

                <div className="suggestions-grid">
                  {suggestions.map((s) => (
                    <SuggestionCard
                      key={s.template_id}
                      suggestion={s}
                      isSelected={selectedSuggestion?.template_id === s.template_id}
                      onSelect={(item) => {
                        setSelectedSuggestion(item);
                        setExecutionResult(null);
                      }}
                    />
                  ))}
                </div>
              </div>
            )}

            {selectedSuggestion && (
              <DynamicPlaceholderForm
                suggestion={selectedSuggestion}
                onExecute={handleExecute}
                executing={executing}
              />
            )}

            {executionResult && <ResultTable result={executionResult} />}
          </>
        )}
      </main>
    </div>
  );
};

export default App;
