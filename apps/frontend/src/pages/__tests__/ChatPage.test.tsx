import { render, screen, fireEvent } from '@testing-library/react';
import { ChatPage } from '../ChatPage';
import { useChatStore } from '@/stores/chatStore';
import type { useChat } from '@/hooks/useChat';

vi.mock('@/stores/chatStore', () => ({
  useChatStore: vi.fn(),
}));

const mockUseChat = vi.fn();
vi.mock('@/hooks/useChat', () => ({
  useChat: () => mockUseChat(),
}));

describe('ChatPage', () => {
  beforeEach(() => {
    HTMLElement.prototype.scrollIntoView = vi.fn();
    
    (useChatStore as any).mockReturnValue({
      messages: [],
      isLoading: false,
      department: 'auto',
      sessionId: 'test-session-123',
      agentTrace: null,
      setDepartment: vi.fn(),
    });

    mockUseChat.mockReturnValue({
      sendMessage: vi.fn(),
      isLoading: false,
      messages: [],
      department: 'auto',
      agentTrace: null,
      setDepartment: vi.fn(),
      clearMessages: vi.fn(),
    });
  });

  it('renders three-section layout', () => {
    const { container } = render(<ChatPage />);
    
    const mainContainer = container.querySelector('.flex.h-screen');
    expect(mainContainer).toBeInTheDocument();
  });

  it('renders DepartmentSelector in left sidebar', () => {
    render(<ChatPage />);
    
    expect(screen.getByLabelText(/department/i)).toBeInTheDocument();
  });

  it('renders ChatMessageList in main area', () => {
    render(<ChatPage />);
    
    const mainArea = screen.getByRole('main');
    expect(mainArea).toBeInTheDocument();
  });

  it('renders ChatInput in main area', () => {
    render(<ChatPage />);
    
    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
  });

  it('does not render AgentTracePanel when agentTrace is null', () => {
    render(<ChatPage />);
    
    expect(screen.queryByText(/agent trace/i)).not.toBeInTheDocument();
  });

  it('renders AgentTracePanel when agentTrace is available', () => {
    (useChatStore as any).mockReturnValue({
      messages: [],
      isLoading: false,
      department: 'auto',
      sessionId: 'test-session-123',
      agentTrace: {
        supervisor_decision: 'Routing to IT Support',
        agents_invoked: ['it_support'],
        retrieval_sources: [],
        iterations: 1,
        confidence: 0.9,
      },
      setDepartment: vi.fn(),
    });

    render(<ChatPage />);
    
    expect(screen.getByText(/agent trace/i)).toBeInTheDocument();
  });

  it('displays messages in ChatMessageList', () => {
    (useChatStore as any).mockReturnValue({
      messages: [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there' },
      ],
      isLoading: false,
      department: 'auto',
      sessionId: 'test-session-123',
      agentTrace: null,
      setDepartment: vi.fn(),
    });

    render(<ChatPage />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there')).toBeInTheDocument();
  });

  it('passes sendMessage to ChatInput', () => {
    const mockSendMessage = vi.fn();
    mockUseChat.mockReturnValue({
      sendMessage: mockSendMessage,
      isLoading: false,
      messages: [],
      department: 'auto',
      agentTrace: null,
      setDepartment: vi.fn(),
      clearMessages: vi.fn(),
    });

    render(<ChatPage />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    expect(mockSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('disables ChatInput when isLoading is true', () => {
    (useChatStore as any).mockReturnValue({
      messages: [],
      isLoading: true,
      department: 'auto',
      sessionId: 'test-session-123',
      agentTrace: null,
      setDepartment: vi.fn(),
    });

    mockUseChat.mockReturnValue({
      sendMessage: vi.fn(),
      isLoading: true,
      messages: [],
      department: 'auto',
      agentTrace: null,
      setDepartment: vi.fn(),
      clearMessages: vi.fn(),
    });

    render(<ChatPage />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('updates department when DepartmentSelector changes', () => {
    const mockSetDepartment = vi.fn();
    mockUseChat.mockReturnValue({
      sendMessage: vi.fn(),
      isLoading: false,
      messages: [],
      department: 'auto',
      agentTrace: null,
      setDepartment: mockSetDepartment,
      clearMessages: vi.fn(),
    });

    render(<ChatPage />);
    
    const departmentSelect = screen.getByLabelText(/department/i);
    fireEvent.change(departmentSelect, { target: { value: 'it_support' } });
    
    expect(mockSetDepartment).toHaveBeenCalledWith('it_support');
  });

  it('maintains responsive layout structure', () => {
    const { container } = render(<ChatPage />);
    
    const sidebar = container.querySelector('aside');
    const main = container.querySelector('main');
    
    expect(sidebar).toBeInTheDocument();
    expect(main).toBeInTheDocument();
  });
});
