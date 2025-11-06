// ===== Helpers =====

/**
 * Formats a date string.
 * If it's an ISO string (from Eventbrite), it formats it.
 * If it's a normal string (from Fatsoma), it leaves it.
 */
function formatEventDate(dateString) {
  // Check if it's a raw ISO string (e.g., "2025-11-22T23:00:00")
  if (dateString && dateString.includes('T') && dateString.startsWith('20')) {
    try {
      const date = new Date(dateString);
      
      // Format the date to "Fri 7 Nov"
      const datePart = date.toLocaleDateString('en-GB', { 
        weekday: 'short', 
        day: 'numeric', 
        month: 'short' 
      });
      
      // Format the time to a simple "9:00pm"
      let hour = date.getHours();
      const minute = date.getMinutes();
      const ampm = hour >= 12 ? 'pm' : 'am';
      hour = hour % 12;
      hour = hour ? hour : 12; // The hour '0' should be '12'
      const minuteStr = minute < 10 ? '0' + minute : minute;
      
      const timePart = `${hour}:${minuteStr}${ampm}`;
      
      return `${datePart} at ${timePart}`; // e.g., "Fri 7 Nov at 9:00pm"
    
    } catch (e) {
      console.error("Could not format date:", dateString);
      return dateString; // Failsafe, return the original string
    }
  }
  
  // It's not an ISO string, so just return it as-is (Fatsoma or "TBA")
  return dateString || 'TBA';
}

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
    // Use a style that matches your site
    resultsDiv.innerHTML = '<p style="color: #ccc; text-align: center;">😢 No matching events found for that vibe. Try a different search.</p>';
    return;
  }

  events.forEach(ev => {
    // Use the event keys from your backend logic (title, venue, date, url)
    const name = ev.title || ev.name || 'Untitled Event';
    const date = formatEventDate(ev.date);
    const location = ev.venue || 'TBA';
    const url = ev.url || '#';

    const card = document.createElement('div');
    card.className = 'event-card';
    card.innerHTML = `
      <h3>${name}</h3>
      <p>📅 ${date}</p>
      <p>📍 ${location}</p>
      <a href="${url}" target="_blank" rel="noopener">View Event</a>
    `;
    resultsDiv.appendChild(card);
  });
}

// ===== Spotify Playlist Form (This is your working, fixed version) =====
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
    
    // Get the city from the location box, default to 'london' if empty
    const city = (document.getElementById('location') || {}).value || 'london';

    // Show only Spotify loader
    loader.style.display = 'flex'; // Use flex to center the bars
    const prefLoader = document.getElementById('loading-preferences');
    if (prefLoader) prefLoader.style.display = 'none';

    resultsDiv.innerHTML = '';

    try {
      const res = await fetch('http://127.0.0.1:5000/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send the playlist_id AND the city variable
        body: JSON.stringify({ playlist_id: playlistId, city: city, top_n: 5 })
      });

      const data = await res.json();
      loader.style.display = 'none';
      displayEvents(data.events); // expects backend to return JSON with an 'events' array
    } catch (err) {
      console.error(err);
      loader.style.display = 'none';
      resultsDiv.innerHTML = '<p style="color:#f88;">Error fetching events from playlist.</p>';
    }
  });
})();

// ===== Preferences Form (MODIFIED) =====
(() => {
  const form = document.getElementById('preferencesForm');
  const loader = document.getElementById('loading-preferences'); // spinner under the Preferences form
  const resultsDiv = document.getElementById('results');

  if (!form || !loader) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // --- 1. READ ALL FORM VALUES ---
    const city = (document.getElementById('location') || {}).value || 'london';
    const genreString = (document.getElementById('genre') || {}).value || '';
    const budget = (document.getElementById('budget') || {}).value || 'any'; // <-- NEW
    const when = (document.getElementById('when') || {}).value || 'any';     // <-- NEW
    
    const keywords = genreString.split(',').filter(g => g.trim() !== '');

    if (keywords.length === 0) {
        resultsDiv.innerHTML = '<p style="color: #ccc; text-align: center;">Please select at least one genre.</p>';
        return;
    }

    // Show only Preferences loader
    loader.style.display = 'flex'; // Use flex to center the bars
    const spotifyLoader = document.getElementById('loading');
    if (spotifyLoader) spotifyLoader.style.display = 'none';

    resultsDiv.innerHTML = '';

    try {
      const res = await fetch('http://127.0.0.1:5000/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        // --- 2. SEND ALL VALUES TO BACKEND ---
        body: JSON.stringify({
            keywords: keywords,
            city: city,
            top_n: 5,
            budget: budget, // <-- NEW
            when: when      // <-- NEW
        })
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