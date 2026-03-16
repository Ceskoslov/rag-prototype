import { render, screen } from '@testing-library/react';
import { SourceList } from '../SourceList';

describe('SourceList', () => {
  it('renders nothing when sources array is empty', () => {
    const { container } = render(<SourceList sources={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders section heading when sources exist', () => {
    const sources = [
      {
        title: 'Test Source',
        snippet: 'Test snippet',
        department: 'it_support' as const,
      },
    ];
    
    render(<SourceList sources={sources} />);
    expect(screen.getByText('Sources')).toBeInTheDocument();
  });

  it('renders all source cards', () => {
    const sources = [
      {
        title: 'Source 1',
        snippet: 'Snippet 1',
        department: 'it_support' as const,
      },
      {
        title: 'Source 2',
        snippet: 'Snippet 2',
        department: 'legal' as const,
      },
      {
        title: 'Source 3',
        snippet: 'Snippet 3',
        department: 'credit_card' as const,
      },
    ];
    
    render(<SourceList sources={sources} />);
    
    expect(screen.getByText('Source 1')).toBeInTheDocument();
    expect(screen.getByText('Source 2')).toBeInTheDocument();
    expect(screen.getByText('Source 3')).toBeInTheDocument();
  });

  it('uses grid layout for source cards', () => {
    const sources = [
      {
        title: 'Test',
        snippet: 'Test',
        department: 'it_support' as const,
      },
    ];
    
    const { container } = render(<SourceList sources={sources} />);
    const grid = container.querySelector('.grid');
    
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2');
  });
});
