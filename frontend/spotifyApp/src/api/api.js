const BASE_URL = "http://192.168.1.88:8000"; 
// If using physical phone: replace with your PC's LAN IP

export async function getLoginUrl() {
  const res = await fetch(`${BASE_URL}/auth/login-url`);
  return res.json();
}

export async function getPlaylist(sessionId, playlistId) {
  const res = await fetch(`${BASE_URL}/playlist/${playlistId}?sessionId=${sessionId}`);
  return res.json();
}

export async function runCluster(sessionId) {
  const res = await fetch(`${BASE_URL}/cluster/run?sessionId=${sessionId}`);
  return res.json();
}

export async function addToQueue(sessionId) {
  const res = await fetch(`${BASE_URL}/queue/add?sessionId=${sessionId}`);
  return res.json();
}

export async function FinishTheQueue(sessionId,numSongs) {
  console.log("This shit got pusshed")
  console.log("id: ",sessionId,"\nSongs: ",numSongs)
  const params = new URLSearchParams({
    sessionId : sessionId,
    queueAddLength : numSongs,
  });
  const res = await fetch(`${BASE_URL}/queue/finish-queue?${params.toString()}`);
  return res.json();
}
