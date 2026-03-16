import React, { useState } from 'react';
import type { AgentTrace } from '@/types/chat';

interface AgentTracePanelProps {
  trace: AgentTrace | null;
}

const departmentColors: Record<string, string> = {
  it_support: 'bg-blue-100 text-blue-800',
  legal: 'bg-purple-100 text-purple-800',
  credit_card: 'bg-green-100 text-green-800',
  airport_ground: 'bg-orange-100 text-orange-800',
};

const departmentLabels: Record<string, string> = {
  it_support: 'IT Support',
  legal: 'Legal',
  credit_card: 'Credit Card',
  airport_ground: 'Airport Ground',
};

export const AgentTracePanel: React.FC<AgentTracePanelProps> = ({ trace }) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    routing: true,
    agents: true,
    sources: true,
  });

  if (!trace) {
    return null;
  }

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  return (
    <aside className="w-96 border-l border-gray-200 p-4 overflow-y-auto bg-gray-50">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Agent Trace</h2>
        <p className="text-sm text-gray-600">System reasoning and sources</p>
      </div>

      <div className="space-y-4">
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('routing')}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">Routing Decision</span>
            <span className="text-gray-400">
              {expandedSections.routing ? '▼' : '▶'}
            </span>
          </button>
          {expandedSections.routing && (
            <div className="px-4 py-3 border-t border-gray-100">
              <p className="text-sm text-gray-700">{trace.supervisor_decision}</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <button
            onClick={() => toggleSection('agents')}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">Agents Invoked</span>
            <span className="text-gray-400">
              {expandedSections.agents ? '▼' : '▶'}
            </span>
          </button>
          {expandedSections.agents && (
            <div className="px-4 py-3 border-t border-gray-100">
              <div className="flex flex-wrap gap-2 mb-3">
                {trace.agents_invoked.map((agent) => (
                  <span
                    key={agent}
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      departmentColors[agent] || 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {departmentLabels[agent] || agent}
                  </span>
                ))}
              </div>
              <div className="space-y-2 text-sm text-gray-700">
                <div className="flex justify-between">
                  <span className="text-gray-600">Iterations:</span>
                  <span className="font-medium">{trace.iterations}</span>
                </div>
                {trace.confidence !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Confidence:</span>
                    <span className="font-medium">
                      {Math.round(trace.confidence * 100)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {trace.retrieval_sources.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => toggleSection('sources')}
              className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
            >
              <span className="font-medium text-gray-900">
                Retrieval Sources ({trace.retrieval_sources.length})
              </span>
              <span className="text-gray-400">
                {expandedSections.sources ? '▼' : '▶'}
              </span>
            </button>
            {expandedSections.sources && (
              <div className="px-4 py-3 border-t border-gray-100 space-y-3">
                {trace.retrieval_sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-sm font-semibold text-gray-900 flex-1">
                        {source.title}
                      </h4>
                      <span
                        className={`ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          departmentColors[source.department] || 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {departmentLabels[source.department] || source.department}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">Relevance Score:</span>
                      <span className="font-medium text-gray-900">
                        {Math.round(source.score * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
