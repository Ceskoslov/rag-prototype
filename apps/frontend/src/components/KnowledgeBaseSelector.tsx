import React from 'react';

interface KnowledgeBaseSelectorProps {
  value: string;
  options: string[];
  onChange: (knowledgeBase: string) => void;
}

const labelFor = (value: string) =>
  value
    .split(/[_-]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

export const KnowledgeBaseSelector: React.FC<KnowledgeBaseSelectorProps> = ({
  value,
  options,
  onChange,
}) => {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="knowledge-base-select" className="text-sm font-medium text-gray-700">
        Knowledge base
      </label>
      <select
        id="knowledge-base-select"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="all">All knowledge bases</option>
        {options.map((name) => (
          <option key={name} value={name}>
            {labelFor(name)}
          </option>
        ))}
      </select>
    </div>
  );
};
