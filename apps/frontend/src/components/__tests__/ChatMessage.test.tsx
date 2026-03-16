import { render, screen } from '@testing-library/react';
import { ChatMessage } from '../ChatMessage';

describe('ChatMessage', () => {
  it('renders user message with blue background', () => {
    render(<ChatMessage role="user" content="Hello" />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders assistant message with gray background', () => {
    render(<ChatMessage role="assistant" content="Hi there" />);
    expect(screen.getByText('Hi there')).toBeInTheDocument();
  });

  it('preserves whitespace with pre-wrap', () => {
    const multilineContent = 'Line 1\nLine 2\nLine 3';
    render(<ChatMessage role="user" content={multilineContent} />);
    expect(screen.getByText(/Line 1/)).toBeInTheDocument();
    expect(screen.getByText(/Line 2/)).toBeInTheDocument();
    expect(screen.getByText(/Line 3/)).toBeInTheDocument();
  });
});
