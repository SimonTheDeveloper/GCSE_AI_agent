import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  it('renders login heading', () => {
    window.localStorage.removeItem('isLoggedIn');
    render(<App />);

    // The default unauthenticated view is the Login screen.
    expect(screen.getByRole('button', { name: /try demo account/i })).toBeInTheDocument();
  });
});
