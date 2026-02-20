import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { App } from '../src/App';

describe('App', () => {
  beforeEach(() => {
    render(<App />);
  });

  it('renders welcome heading', () => {
    const heading = screen.getByRole('heading', {
      name: /Caringbah Social Golf Club/i,
    });
    expect(heading).toBeDefined();
  });

  it('renders features list', () => {
    const featuresList = screen.getByText(/Features:/i);
    expect(featuresList).toBeDefined();
  });

  it('displays React 19 feature', () => {
    const feature = screen.getByText(/React 19 with TypeScript/i);
    expect(feature).toBeDefined();
  });

  it('displays welcome message', () => {
    const welcomeMessage = screen.getByText(/minimal React 19 \+ TypeScript \+ Vite application/i);
    expect(welcomeMessage).toBeDefined();
  });

  it('renders login section when logged out', () => {
    // Google Identity Services will render the button at runtime
    // In the test environment, we just verify the container and heading exist
    const loginHeading = screen.getByRole('heading', { name: /login/i });
    expect(loginHeading).toBeDefined();
  });
});
