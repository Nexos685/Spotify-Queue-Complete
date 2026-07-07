import AsyncStorage from '@react-native-async-storage/async-storage';

export async function saveSessionId(id) {
  await AsyncStorage.setItem('session_id', id);
}

export async function getSessionId() {
  return await AsyncStorage.getItem('session_id');
}