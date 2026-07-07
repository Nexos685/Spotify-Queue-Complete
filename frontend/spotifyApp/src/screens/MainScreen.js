import React, { useState } from 'react';
import { View, TextInput, Pressable, Text, StyleSheet, SafeAreaView, ScrollView } from 'react-native';
import { getPlaylist, runCluster, addToQueue, FinishTheQueue } from '../api/api';

// Add new buttons here — just drop another ActionButton into the return below
function ActionButton({ label, onPress, variant = 'primary' }) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        styles[variant],
        pressed && styles[`${variant}Pressed`],
      ]}
    >
      <Text style={[styles.buttonText, variant === 'secondary' && styles.secondaryText]}>
        {label}
      </Text>
    </Pressable>
  );
}

export default function MainScreen({ sessionId }) {
  const [numSongsToAdd, setNumSongs] = useState('15');

  const handleNumChange = (text) => {
    const cleaned = text.replace(/[^0-9]/g, '');
    setNumSongs(cleaned);
  };

  const handleBlur = () => {
    if (numSongsToAdd === '') setNumSongs('15');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>

        <Text style={styles.heading}>VIBEQUEUE</Text>
        <Text style={styles.subheading}>Session Controls</Text>

        {/* ── Buttons ── add more ActionButtons here as needed */}
        <View style={styles.buttonGroup}>
          <ActionButton
            label="Finish the Queue"
            onPress={() => FinishTheQueue(sessionId, numSongsToAdd)}
          />
          <ActionButton
            label="Fetch Playlist"
            onPress={() => getPlaylist(sessionId)}
            variant="secondary"
          />
          <ActionButton
            label="Run Clustering"
            onPress={() => runCluster(sessionId)}
            variant="secondary"
          />
        </View>

        {/* ── Number input ── */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Songs to add</Text>
          <TextInput
            value={numSongsToAdd}
            onChangeText={handleNumChange}
            onBlur={handleBlur}
            keyboardType="numeric"
            placeholder="Default: 15"
            placeholderTextColor="#555"
            style={styles.input}
          />
        </View>

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
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingVertical: 40,
    gap: 24,
  },
  heading: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '800',
    letterSpacing: 6,
    textAlign: 'center',
  },
  subheading: {
    color: '#555',
    fontSize: 13,
    letterSpacing: 1,
    textAlign: 'center',
    marginTop: -16,
  },

  // Button group
  buttonGroup: {
    gap: 12,
    marginTop: 8,
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 50,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.4,
  },

  // Primary variant (Spotify green)
  primary: {
    backgroundColor: '#1DB954',
  },
  primaryPressed: {
    backgroundColor: '#17a348',
  },

  // Secondary variant (outlined)
  secondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#333',
  },
  secondaryPressed: {
    backgroundColor: '#1a1a1a',
  },
  secondaryText: {
    color: '#999',
  },

  // Input
  inputGroup: {
    gap: 8,
  },
  inputLabel: {
    color: '#666',
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  input: {
    backgroundColor: '#1A1A1A',
    borderWidth: 1,
    borderColor: '#2A2A2A',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: '#FFFFFF',
  },
});