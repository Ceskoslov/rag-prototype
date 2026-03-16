import { render, screen } from '@testing-library/react';
import { SourceCard } from '../SourceCard';

describe('SourceCard', () => {
  it('renders title, snippet, and department badge', () => {
    render(
      <SourceCard
        title="VPN Setup Guide"
        snippet="Follow these steps to configure VPN access..."
        department="it_support"
      />
    );
    
    expect(screen.getByText('VPN Setup Guide')).toBeInTheDocument();
    expect(screen.getByText('Follow these steps to configure VPN access...')).toBeInTheDocument();
    expect(screen.getByText('IT Support')).toBeInTheDocument();
  });

  it('applies correct color for IT Support department', () => {
    const { container } = render(
      <SourceCard
        title="Test"
        snippet="Test snippet"
        department="it_support"
      />
    );
    
    const badge = screen.getByText('IT Support');
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
  });

  it('applies correct color for Legal department', () => {
    const { container } = render(
      <SourceCard
        title="Test"
        snippet="Test snippet"
        department="legal"
      />
    );
    
    const badge = screen.getByText('Legal');
    expect(badge).toHaveClass('bg-purple-100', 'text-purple-800');
  });

  it('applies correct color for Credit Card department', () => {
    const { container } = render(
      <SourceCard
        title="Test"
        snippet="Test snippet"
        department="credit_card"
      />
    );
    
    const badge = screen.getByText('Credit Card');
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('applies correct color for Airport Ground department', () => {
    const { container } = render(
      <SourceCard
        title="Test"
        snippet="Test snippet"
        department="airport_ground"
      />
    );
    
    const badge = screen.getByText('Airport Ground');
    expect(badge).toHaveClass('bg-orange-100', 'text-orange-800');
  });

  it('renders as article element for semantic HTML', () => {
    const { container } = render(
      <SourceCard
        title="Test"
        snippet="Test snippet"
        department="it_support"
      />
    );
    
    expect(container.querySelector('article')).toBeInTheDocument();
  });
});
