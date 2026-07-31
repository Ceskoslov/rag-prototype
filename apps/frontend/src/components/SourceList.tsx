import React from 'react';
import { SourceCard } from './SourceCard';

interface Source {
  title: string;
  snippet: string;
  knowledge_base: string;
}

interface SourceListProps {
  sources: Source[];
}

export const SourceList: React.FC<SourceListProps> = ({ sources }) => {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">Sources</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sources.map((source, idx) => (
          <SourceCard
            key={idx}
            title={source.title}
            snippet={source.snippet}
            knowledgeBase={source.knowledge_base}
          />
        ))}
      </div>
    </div>
  );
};
