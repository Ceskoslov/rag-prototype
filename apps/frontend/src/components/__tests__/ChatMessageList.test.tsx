import { render, screen } from '@testing-library/react';
import { ChatMessageList } from '../ChatMessageList';

describe('ChatMessageList', () => {
  beforeEach(() => {
    // Mock scrollIntoView which is not available in JSDOM
    HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('renders empty list correctly', () => {
    const { container } = render(<ChatMessageList messages={[]} />);
    expect(container.querySelector('.flex.flex-col')).toBeInTheDocument();
  });

  it('renders multiple messages', () => {
    const messages = [
      { role: 'user' as const, content: 'Hello' },
      { role: 'assistant' as const, content: 'Hi there' },
      { role: 'user' as const, content: 'How are you?' },
    ];
    
    render(<ChatMessageList messages={messages} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there')).toBeInTheDocument();
    expect(screen.getByText('How are you?')).toBeInTheDocument();
  });

  it('scrolls to bottom when messages change', () => {
    const messages = [
      { role: 'user' as const, content: 'Message 1' },
    ];
    
    const scrollIntoViewMock = vi.fn();
    HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;
    
    const { rerender } = render(<ChatMessageList messages={messages} />);
    
    const updatedMessages = [
      ...messages,
      { role: 'assistant' as const, content: 'Message 2' },
    ];
    
    rerender(<ChatMessageList messages={updatedMessages} />);
    
    expect(scrollIntoViewMock).toHaveBeenCalled();
  });
});
