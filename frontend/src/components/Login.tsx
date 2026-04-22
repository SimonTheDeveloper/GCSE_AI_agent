import { useState } from 'react';
import { LoginView } from './views/LoginView';
import { signIn } from '../lib/cognito';
import { toast } from 'sonner';

interface LoginProps {
  onLoginSuccess: () => void;
  onSignUpClick?: () => void;
}

export function Login({ onLoginSuccess, onSignUpClick: _onSignUpClick }: LoginProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      const { email: resolvedEmail } = await signIn(email, password);
      localStorage.setItem('userEmail', resolvedEmail);
      onLoginSuccess();
    } catch (err: unknown) {
      const code = (err as { code?: string }).code;
      if (code === 'NotAuthorizedException' || code === 'UserNotFoundException') {
        setError('Incorrect email or password.');
      } else if (code === 'UserNotConfirmedException') {
        setError('Please verify your email address before signing in.');
      } else if (code === 'NEW_PASSWORD_REQUIRED') {
        setError('A new password is required. Please contact the administrator.');
      } else {
        setError('Sign in failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUpClick = () => {
    toast.info('Access is by invitation only. Contact the administrator to request access.');
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
      onDemoLogin={undefined}
      onSignUpClick={handleSignUpClick}
    />
  );
}
