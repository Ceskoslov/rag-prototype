import React from 'react';

type Department = 'it_support' | 'legal' | 'credit_card' | 'airport_ground';

interface SourceCardProps {
  title: string;
  snippet: string;
  department: Department;
}

const departmentColors: Record<Department, string> = {
  it_support: 'bg-blue-100 text-blue-800',
  legal: 'bg-purple-100 text-purple-800',
  credit_card: 'bg-green-100 text-green-800',
  airport_ground: 'bg-orange-100 text-orange-800',
};

const departmentLabels: Record<Department, string> = {
  it_support: 'IT Support',
  legal: 'Legal',
  credit_card: 'Credit Card',
  airport_ground: 'Airport Ground',
};

export const SourceCard: React.FC<SourceCardProps> = ({ title, snippet, department }) => {
  return (
    <article className="border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">{title}</h3>
        <span className={`ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${departmentColors[department]}`}>
          {departmentLabels[department]}
        </span>
      </div>
      <p className="text-xs text-gray-600 line-clamp-3">{snippet}</p>
    </article>
  );
};
