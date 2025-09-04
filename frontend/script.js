// ===== Helpers =====
function extractPlaylistId(url) {
  // Accept full URL or raw ID
  try {
    const parts = url.split('/');
    const last = parts[parts.length - 1];
    return last.split('?')[0];
  } catch {
    return url.trim();
  }
}

function displayEvents(events) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (!events || events.length === 0) {
    resultsDiv.innerHTML = '<p>No events found. Try a different search.</p>';
    return;
  }

  events.forEach(ev => {
    const name = ev.name || 'Event';
    const date = ev.date || ev.startDate || 'TBA';
    const location = ev.location || ev.venue || 'TBA';
    const url = ev.ticketUrl || ev.url || '#';

    const card = document.createElement('div');
    card.className = 'event-card';
    card.innerHTML = `
      <h3>${name}</h3>
      <p>${date} | ${location}</p>
      <a href="${url}" target="_blank" rel="noopener">Buy Tickets</a>
    `;
    resultsDiv.appendChild(card);
  });
}

// ===== Spotify Playlist Form =====
(() => {
  const form = document.getElementById('spotifyForm');
  const loader = document.getElementById('loading'); // spinner under the Spotify form
  const resultsDiv = document.getElementById('results');

  if (!form || !loader) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const playlistUrlInput = document.getElementById('playlistUrl');
    if (!playlistUrlInput) return;

    const playlistUrl = playlistUrlInput.value.trim();
    if (!playlistUrl) return;

    const playlistId = extractPlaylistId(playlistUrl);

    // Show only Spotify loader
    loader.style.display = 'block';
    const prefLoader = document.getElementById('loading-preferences');
    if (prefLoader) prefLoader.style.display = 'none';

    resultsDiv.innerHTML = '';

    try {
      const res = await fetch('http://localhost:5000/api/playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlistId })
      });

      const data = await res.json();
      loader.style.display = 'none';
      displayEvents(data.events);
    } catch (err) {
      console.error(err);
      loader.style.display = 'none';
      resultsDiv.innerHTML = '<p style="color:#f88;">Error fetching events from playlist.</p>';
    }
  });
})();

// ===== Preferences Form =====
(() => {
  const form = document.getElementById('preferencesForm');
  const loader = document.getElementById('loading-preferences'); // spinner under the Preferences form
  const resultsDiv = document.getElementById('results');

  if (!form || !loader) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const budget = (document.getElementById('budget') || {}).value || 'any';
    const location = (document.getElementById('location') || {}).value || '';
    const genre = (document.getElementById('genre') || {}).value || 'any';
    const when = (document.getElementById('when') || {}).value || 'any';

    // Show only Preferences loader
    loader.style.display = 'block';
    const spotifyLoader = document.getElementById('loading');
    if (spotifyLoader) spotifyLoader.style.display = 'none';

    resultsDiv.innerHTML = '';

    try {
      const res = await fetch('http://localhost:5000/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget, location, genre, when })
      });

      const data = await res.json();
      loader.style.display = 'none';
      displayEvents(data.events);
    } catch (err) {
      console.error(err);
      loader.style.display = 'none';
      resultsDiv.innerHTML = '<p style="color:#f88;">Error fetching events from preferences.</p>';
    }
  });
})();
