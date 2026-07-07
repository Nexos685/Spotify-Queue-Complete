import React, { useEffect, useState } from 'react';
import { Linking } from 'react-native';
import LoginScreen from './src/screens/LoginScreen';
import MainScreen from './src/screens/MainScreen';
import { saveSessionId, getSessionId } from './src/storage/session';

export default function App() {
  const [sessionId, setSessionId] = useState(null);

  function handleLogin(id) {
    console.log("Logged in successfully with session:", id);
    setSessionId(id); // Save it to state to unlock the rest of your app
  }

  useEffect(() => {
    // Load saved session
    getSessionId().then(id => {
      if (id) setSessionId(id);
    });

    // Handle incoming deep links
    const sub = Linking.addEventListener('url', ({ url }) => {
      try {
        const parsed = new URL(url);
        const id = parsed.searchParams.get('session_id');

        if (id) {
          saveSessionId(id);
          setSessionId(id);
        }
      } catch (e) {
        console.log('Failed to parse URL:', e);
      }
    });

    return () => {
      sub.remove();
    };
  }, []);

  if (!sessionId) return <LoginScreen onLogin={handleLogin} />;
  return <MainScreen sessionId={sessionId} />;
}
