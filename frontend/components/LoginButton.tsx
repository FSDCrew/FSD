"use client"

import { signInWithRedirect } from 'aws-amplify/auth';
import { useAuth } from '../contexts/AuthContext';
import { Button } from "@/components/ui/button";

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
        <Button
          onClick={handleLogin}
        >
          Sign In
        </Button>
      ) : (
        <>Logged In</>
      )}
    </>
  );
};

export default LoginButton;