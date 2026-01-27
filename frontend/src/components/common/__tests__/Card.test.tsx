import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Card from '../Card';

describe('Card Component', () => {
  it('renders title and children correctly', () => {
    render(
      <Card title="Test Card">
        <p>Card content</p>
      </Card>
    );
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies custom className correctly', () => {
    render(
      <Card title="Test" className="custom-class">
        Content
      </Card>
    );
    const cardElement = screen.getByText('Test').closest('.bg-white');
    expect(cardElement).toHaveClass('custom-class');
  });
});
