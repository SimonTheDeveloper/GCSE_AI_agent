import { useState } from 'react';
import { LoginView } from './views/LoginView';

interface LoginProps {
  onLoginSuccess: () => void;
  onSignUpClick?: () => void;
}

export function Login({ onLoginSuccess, onSignUpClick }: LoginProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    setIsLoading(true);

    // Mock authentication - in production, this would call a real API
    setTimeout(() => {
      if (email && password.length >= 6) {
        // Store login state
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('userEmail', email);
        if (rememberMe) {
          localStorage.setItem('rememberMe', 'true');
        }
        onLoginSuccess();
      } else {
        setError('Invalid credentials. Please try again.');
        setIsLoading(false);
      }
    }, 1000);
  };

  const handleDemoLogin = () => {
    setEmail('demo@student.com');
    setPassword('demo123');
    setIsLoading(true);

    setTimeout(() => {
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userEmail', 'demo@student.com');
      localStorage.setItem('userName', 'Demo Student');
      onLoginSuccess();
    }, 800);
  };

  return (
    <LoginView
      email={email}
      password={password}
      rememberMe={rememberMe}
      error={error}
      isLoading={isLoading}
      onEmailChange={setEmail}
      onPasswordChange={setPassword}
      onRememberMeChange={setRememberMe}
      onSubmit={handleSubmit}
      onDemoLogin={handleDemoLogin}
      onSignUpClick={onSignUpClick}
    />
  );
}
