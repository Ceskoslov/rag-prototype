import React from 'react';

interface SourceCardProps {
  title: string;
  snippet: string;
  knowledgeBase: string;
}

export const SourceCard: React.FC<SourceCardProps> = ({ title, snippet, knowledgeBase }) => {
  return (
    <article className="border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">{title}</h3>
        <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {knowledgeBase}
        </span>
      </div>
      <p className="text-xs text-gray-600 line-clamp-3">{snippet}</p>
    </article>
  );
};
