"use client"

import { signInWithRedirect } from 'aws-amplify/auth';
import { useAuth } from '../contexts/AuthContext';

const LoginButton = () => {
  const { isAuthenticated } = useAuth();

  const handleLogin = async () => {
    try {
      await signInWithRedirect();
    } catch (error) {
      console.error('Error signing in:', error);
    }
  };

  return (
    <>
      {!isAuthenticated ? (
        <button 
          onClick={handleLogin}
          className="w-full px-4 py-2 bg-black text-white rounded hover:bg-blue-600"
        >
          Sign In
        </button>
      ) : (
        <>Logged In</>
      )}
    </>
  );
};

export default LoginButton;