import React from 'react';

type Department = 'it_support' | 'legal' | 'credit_card' | 'airport_ground' | 'auto';

interface DepartmentSelectorProps {
  value: Department;
  onChange: (department: Department) => void;
}

const departments: { value: Department; label: string }[] = [
  { value: 'auto', label: 'Auto (Let AI decide)' },
  { value: 'it_support', label: 'IT Support' },
  { value: 'legal', label: 'Legal' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'airport_ground', label: 'Airport Ground Services' },
];

export const DepartmentSelector: React.FC<DepartmentSelectorProps> = ({ value, onChange }) => {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="department-select" className="text-sm font-medium text-gray-700">
        Department
      </label>
      <select
        id="department-select"
        value={value}
        onChange={(e) => onChange(e.target.value as Department)}
        className="border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {departments.map((dept) => (
          <option key={dept.value} value={dept.value}>
            {dept.label}
          </option>
        ))}
      </select>
    </div>
  );
};
