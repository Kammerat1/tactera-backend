import React, { useState } from 'react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { api } from '../services/api';

type AuthMode = 'login' | 'register';

type AuthContainerProps = {
  onAuthSuccess: (userData: any) => void;
};

export const AuthContainer = ({ onAuthSuccess }: AuthContainerProps) => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.auth.login(email, password);
      
      // Store authentication data (you might want to use localStorage or a context)
      localStorage.setItem('authToken', response.token || 'mock-token');
      localStorage.setItem('userEmail', email);
      
      onAuthSuccess(response);
    } catch (err: any) {
      console.error('Login failed:', err);
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (email: string, password: string, managerName: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.auth.register(email, password, managerName);
      
      // Store authentication data
      localStorage.setItem('authToken', response.token || 'mock-token');
      localStorage.setItem('userEmail', email);
      localStorage.setItem('managerName', managerName);
      
      onAuthSuccess(response);
    } catch (err: any) {
      console.error('Registration failed:', err);
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const switchToRegister = () => {
    setMode('register');
    setError(null);
  };

  const switchToLogin = () => {
    setMode('login');
    setError(null);
  };

  if (mode === 'login') {
    return (
      <LoginForm
        onLogin={handleLogin}
        onSwitchToRegister={switchToRegister}
        isLoading={isLoading}
        error={error}
      />
    );
  }

  return (
    <RegisterForm
      onRegister={handleRegister}
      onSwitchToLogin={switchToLogin}
      isLoading={isLoading}
      error={error}
    />
  );
};