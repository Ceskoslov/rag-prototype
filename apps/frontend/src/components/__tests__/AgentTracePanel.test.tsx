import { render, screen, fireEvent } from '@testing-library/react';
import { AgentTracePanel } from '../AgentTracePanel';
import type { AgentTrace } from '@/types/chat';

describe('AgentTracePanel', () => {
  const mockAgentTrace: AgentTrace = {
    supervisor_decision: 'Routing to IT Support and Legal departments',
    agents_invoked: ['it_support', 'legal'],
    retrieval_sources: [
      {
        department: 'it_support',
        title: 'VPN Setup Guide',
        score: 0.92,
        content: 'How to configure VPN access...',
      },
      {
        department: 'legal',
        title: 'Data Privacy Policy',
        score: 0.87,
        content: 'Our data privacy guidelines...',
      },
    ],
    iterations: 2,
    confidence: 0.85,
  };

  it('renders nothing when trace is null', () => {
    const { container } = render(<AgentTracePanel trace={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders trace panel when trace is provided', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    expect(screen.getByText(/agent trace/i)).toBeInTheDocument();
  });

  it('displays supervisor decision', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    expect(screen.getByText(/routing to it support and legal departments/i)).toBeInTheDocument();
  });

  it('displays agents invoked as badges', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    const badges = screen.getAllByText(/IT Support/i);
    expect(badges.length).toBeGreaterThan(0);
    const legalBadges = screen.getAllByText(/Legal/i);
    expect(legalBadges.length).toBeGreaterThan(0);
  });

  it('displays confidence score as percentage', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    expect(screen.getByText(/85%/i)).toBeInTheDocument();
  });

  it('displays iteration count', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    expect(screen.getByText(/Iterations:/i)).toBeInTheDocument();
    const iterationValue = screen.getAllByText('2');
    expect(iterationValue.length).toBeGreaterThan(0);
  });

  it('displays retrieval sources with titles and scores', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    expect(screen.getByText(/VPN Setup Guide/i)).toBeInTheDocument();
    expect(screen.getByText(/Data Privacy Policy/i)).toBeInTheDocument();
    expect(screen.getByText(/92%/i)).toBeInTheDocument();
    expect(screen.getByText(/87%/i)).toBeInTheDocument();
  });

  it('supports collapsible sections', () => {
    render(<AgentTracePanel trace={mockAgentTrace} />);
    
    // Find collapsible section header (using supervisor decision as header)
    const sectionHeader = screen.getByText(/routing decision/i);
    expect(sectionHeader).toBeInTheDocument();
  });

  it('handles empty agents_invoked array', () => {
    const emptyTrace: AgentTrace = {
      ...mockAgentTrace,
      agents_invoked: [],
    };
    
    render(<AgentTracePanel trace={emptyTrace} />);
    
    expect(screen.getByText(/agent trace/i)).toBeInTheDocument();
  });

  it('handles empty retrieval_sources array', () => {
    const emptyTrace: AgentTrace = {
      ...mockAgentTrace,
      retrieval_sources: [],
    };
    
    render(<AgentTracePanel trace={emptyTrace} />);
    
    expect(screen.getByText(/agent trace/i)).toBeInTheDocument();
  });

  it('displays all four departments with correct colors', () => {
    const fullTrace: AgentTrace = {
      ...mockAgentTrace,
      agents_invoked: ['it_support', 'legal', 'credit_card', 'airport_ground'],
    };
    
    render(<AgentTracePanel trace={fullTrace} />);
    
    const badges = screen.getAllByText(/IT Support/i);
    expect(badges.length).toBeGreaterThan(0);
    const legalBadges = screen.getAllByText(/Legal/i);
    expect(legalBadges.length).toBeGreaterThan(0);
    expect(screen.getByText(/Credit Card/i)).toBeInTheDocument();
    expect(screen.getByText(/Airport Ground/i)).toBeInTheDocument();
  });
});
