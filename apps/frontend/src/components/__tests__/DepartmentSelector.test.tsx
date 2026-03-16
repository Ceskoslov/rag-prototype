import { render, screen, fireEvent } from '@testing-library/react';
import { DepartmentSelector } from '../DepartmentSelector';

describe('DepartmentSelector', () => {
  it('renders all department options', () => {
    const mockOnChange = vi.fn();
    render(<DepartmentSelector value="auto" onChange={mockOnChange} />);
    
    const select = screen.getByLabelText('Department');
    expect(select).toBeInTheDocument();
    
    expect(screen.getByText('Auto (Let AI decide)')).toBeInTheDocument();
    expect(screen.getByText('IT Support')).toBeInTheDocument();
    expect(screen.getByText('Legal')).toBeInTheDocument();
    expect(screen.getByText('Credit Card')).toBeInTheDocument();
    expect(screen.getByText('Airport Ground Services')).toBeInTheDocument();
  });

  it('displays the selected value', () => {
    const mockOnChange = vi.fn();
    render(<DepartmentSelector value="it_support" onChange={mockOnChange} />);
    
    const select = screen.getByLabelText('Department') as HTMLSelectElement;
    expect(select.value).toBe('it_support');
  });

  it('calls onChange when selection changes', () => {
    const mockOnChange = vi.fn();
    render(<DepartmentSelector value="auto" onChange={mockOnChange} />);
    
    const select = screen.getByLabelText('Department');
    fireEvent.change(select, { target: { value: 'legal' } });
    
    expect(mockOnChange).toHaveBeenCalledWith('legal');
  });

  it('renders with accessible label', () => {
    const mockOnChange = vi.fn();
    render(<DepartmentSelector value="auto" onChange={mockOnChange} />);
    
    expect(screen.getByLabelText('Department')).toBeInTheDocument();
  });
});
