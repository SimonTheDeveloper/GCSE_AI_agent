import { useState } from 'react';
import { SignUpView } from './views/SignUpView';

interface SignUpProps {
  onSignUpSuccess: () => void;
  onLoginClick: () => void;
}

export function SignUp({ onSignUpSuccess, onLoginClick }: SignUpProps) {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    gradeLevel: ''
  });
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [passwordStrength, setPasswordStrength] = useState<'weak' | 'medium' | 'strong' | null>(null);

  const validatePassword = (password: string) => {
    if (password.length === 0) {
      setPasswordStrength(null);
      return;
    }
    
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    const criteriaCount = [hasUpperCase, hasLowerCase, hasNumbers, hasSpecialChar].filter(Boolean).length;
    
    if (password.length < 6) {
      setPasswordStrength('weak');
    } else if (password.length >= 8 && criteriaCount >= 3) {
      setPasswordStrength('strong');
    } else {
      setPasswordStrength('medium');
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    if (field === 'password') {
      validatePassword(value);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!formData.fullName.trim()) {
      setError('Please enter your full name');
      return;
    }

    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!formData.gradeLevel) {
      setError('Please select your grade level');
      return;
    }

    if (!acceptTerms) {
      setError('You must accept the terms and conditions');
      return;
    }

    setIsLoading(true);

    // Mock account creation - in production, this would call a real API
    setTimeout(() => {
      // Store user data in localStorage for demo purposes
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userEmail', formData.email);
      localStorage.setItem('userName', formData.fullName);
      localStorage.setItem('userGradeLevel', formData.gradeLevel);
      onSignUpSuccess();
    }, 1500);
  };

  return (
    <SignUpView
      formData={formData}
      acceptTerms={acceptTerms}
      error={error}
      isLoading={isLoading}
      passwordStrength={passwordStrength}
      onFormDataChange={handleInputChange}
      onAcceptTermsChange={setAcceptTerms}
      onSubmit={handleSubmit}
      onLoginClick={onLoginClick}
    />
  );
}
