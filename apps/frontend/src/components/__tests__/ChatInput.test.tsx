import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput', () => {
  it('renders input field and send button', () => {
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} />);
    
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
  });

  it('calls onSend when send button is clicked', () => {
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    expect(mockOnSend).toHaveBeenCalledWith('Test message');
  });

  it('calls onSend when Enter key is pressed', () => {
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });
    
    expect(mockOnSend).toHaveBeenCalledWith('Test message');
  });

  it('clears input after sending', () => {
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    expect(input.value).toBe('');
  });

  it('disables input when disabled prop is true', () => {
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} disabled={true} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('does not send empty or whitespace-only messages', () => {
    const mockOnSend = vi.fn();
    render(<ChatInput onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.click(sendButton);
    
    expect(mockOnSend).not.toHaveBeenCalled();
  });
});
