import { useEffect, useRef } from 'react';
import * as WebBrowser from 'expo-web-browser';
import { makeRedirectUri, useAuthRequest } from 'expo-auth-session';
import { Animated, Pressable, Text, View, StyleSheet, SafeAreaView, ScrollView } from 'react-native';

WebBrowser.maybeCompleteAuthSession();

const discovery = {
  authorizationEndpoint: 'https://accounts.spotify.com/authorize',
  tokenEndpoint: 'https://accounts.spotify.com/api/token',
};

// Animated equalizer bar
function EqBar({ delay, height }) {
  const anim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 600, delay, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0.3, duration: 600, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        width: 4,
        height,
        backgroundColor: '#1DB954',
        borderRadius: 2,
        transform: [{ scaleY: anim }],
        opacity: anim,
      }}
    />
  );
}

export default function LoginScreen({ onLogin }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 1500, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1500, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const [request, response, promptAsync] = useAuthRequest(
    {
      clientId: 'cc625a42f8e140169e7677eec5a33f1f',
      scopes: [
        'user-read-playback-state',
        'user-read-currently-playing',
        'user-modify-playback-state',
        'playlist-read-private',
        'playlist-read-collaborative',
      ],
      redirectUri: makeRedirectUri({ scheme: 'myapp', path: 'redirect' }),
      responseType: 'code',
    },
    discovery
  );

  useEffect(() => {
    if (response?.type === 'success') {
      const { code } = response.params;
      exchangeCodeForSession(code);
    }
  }, [response]);

  async function exchangeCodeForSession(code) {
    try {
      const sessionRes = await fetch('http://192.168.1.88:8000/session/create_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          redirect_uri: request.redirectUri,
          code_verifier: request.codeVerifier,
        }),
      });
      if (!sessionRes.ok) throw new Error('Backend failed to create session');
      const data = await sessionRes.json();
      onLogin(data.session_id);
    } catch (error) {
      console.error('Error exchanging code with backend:', error);
    }
  }

  const eqBars = [
    { delay: 0,   height: 20 },
    { delay: 150, height: 38 },
    { delay: 300, height: 24 },
    { delay: 100, height: 44 },
    { delay: 250, height: 16 },
    { delay: 50,  height: 32 },
    { delay: 200, height: 48 },
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>

        <View style={styles.eqContainer}>
          {eqBars.map((bar, i) => (
            <EqBar key={i} delay={bar.delay} height={bar.height} />
          ))}
        </View>

        <Animated.View style={[styles.iconRing, { transform: [{ scale: pulseAnim }] }]}>
          <View style={styles.iconInner}>
            <Text style={styles.iconEmoji}>♪</Text>
          </View>
        </Animated.View>

        <View style={styles.textArea}>
          <Text style={styles.appName}>VIBEQUEUE</Text>
          <Text style={styles.tagline}>Your Queue.</Text>
          <Text style={styles.tagline}>Your Playlist.</Text>
          <Text style={styles.tagline}>Your Vibe.</Text>
        </View>

        <Pressable
          disabled={!request}
          onPress={() => promptAsync()}
          style={({ pressed }) => [
            styles.loginButton,
            pressed && styles.loginButtonPressed,
            !request && styles.loginButtonDisabled,
          ]}
        >
          <Text style={styles.loginButtonText}>Continue with Spotify</Text>
        </Pressable>

        <Text style={styles.disclaimer}>
          We'll use your Spotify account to manage your queue.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0D0D0D',
  },
  container: {
    flexGrow: 1,              // lets ScrollView stretch to fill height
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingVertical: 40,      // breathing room top and bottom
    gap: 24,
  },
  eqContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 6,
    height: 50,
    marginBottom: 8,
  },
  iconRing: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 2,
    borderColor: '#1DB954',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconInner: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#1A1A1A',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 36,
    color: '#1DB954',
  },
  textArea: {
    alignItems: 'center',
    gap: 8,
  },
  appName: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '800',
    letterSpacing: 8,
    paddingRight:8,
  },
  tagline: {
    color: '#666666',
    fontSize: 14,
    letterSpacing: 1,
    textAlign: 'center',
    width:100
  },
  loginButton: {
    backgroundColor: '#1DB954',
    paddingVertical: 16,
    borderRadius: 50,
    marginTop: 8,
    width: '100%',
    alignItems: 'center',
  },
  loginButtonPressed: {
    backgroundColor: '#17a348',
  },
  loginButtonDisabled: {
    opacity: 0.4,
  },
  loginButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  disclaimer: {
    color: '#333333',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});