import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../src/App';

describe('App', () => {
  it('renders welcome heading', () => {
    render(<App />);
    const heading = screen.getByRole('heading', {
      name: /Caringbah Social Golf Club/i,
    });
    expect(heading).toBeDefined();
  });

  it('renders features list', () => {
    render(<App />);
    const featuresList = screen.getByText(/Features:/i);
    expect(featuresList).toBeDefined();
  });

  it('displays React 19 feature', () => {
    render(<App />);
    const feature = screen.getByText(/React 19 with TypeScript/i);
    expect(feature).toBeDefined();
  });

  it('displays welcome message', () => {
    render(<App />);
    const welcomeMessage = screen.getByText(/minimal React 19 \+ TypeScript \+ Vite application/i);
    expect(welcomeMessage).toBeDefined();
  });
});
