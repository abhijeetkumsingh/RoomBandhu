/* ══════════════════════════════════════════
   MAIN.JS — Room Bandhu
══════════════════════════════════════════ */

/* ── Nav toggle ───────────────────────── */
function toggleMenu() {
  const nav = document.getElementById('nav-links');
  const ham = document.getElementById('hamburger');
  if (nav) nav.classList.toggle('open');
  if (ham) ham.classList.toggle('active');
}

function toggleUserMenu() {
  document.getElementById('user-dropdown')?.classList.toggle('open');
}

document.addEventListener('click', (e) => {
  const dd = document.getElementById('user-dropdown');
  const av = document.querySelector('.user-avatar');
  if (dd && !dd.contains(e.target) && av && !av.contains(e.target)) {
    dd.classList.remove('open');
  }
  // Close mobile nav on outside click
  const nav = document.getElementById('nav-links');
  const ham = document.getElementById('hamburger');
  if (nav && nav.classList.contains('open')) {
    if (!nav.contains(e.target) && ham && !ham.contains(e.target)) {
      nav.classList.remove('open');
      ham.classList.remove('active');
    }
  }
});

/* ── Auto-hide flash messages ─────────── */
document.querySelectorAll('.flash').forEach(f => {
  setTimeout(() => f.style.opacity = '0', 3500);
  setTimeout(() => f.remove(), 4000);
});

/* ── Wishlist toggle (AJAX) ───────────── */
function toggleWish(btn, roomId) {
  fetch(`/wishlist/toggle/${roomId}`, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) { window.location = '/login'; return; }
    btn.classList.toggle('active', data.saved);
    btn.textContent = data.saved ? '❤️' : '🤍';
    const badge = document.getElementById('wish-badge');
    if (badge) badge.textContent = data.count;
    showToast(data.saved ? '❤ Saved to wishlist!' : 'Removed from wishlist');
  })
  .catch(() => window.location = '/login');
}

/* ── Toast notification ───────────────── */
let toastTimer;
function showToast(msg) {
  let t = document.getElementById('toast-msg');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast-msg';
    t.style.cssText = `
      position:fixed;bottom:24px;right:20px;background:#0F1923;color:#fff;
      padding:12px 20px;border-radius:12px;font-size:14px;z-index:999;
      transform:translateY(80px);opacity:0;transition:all 0.3s;
      pointer-events:none;max-width:280px;font-family:'Plus Jakarta Sans',sans-serif;
      box-shadow:0 8px 32px rgba(0,0,0,0.25);
    `;
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.transform = 'translateY(0)';
  t.style.opacity = '1';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.style.transform = 'translateY(80px)';
    t.style.opacity = '0';
  }, 2800);
}

/* ── Star rating input ────────────────── */
function initStarRating(containerId, inputId) {
  const container = document.getElementById(containerId);
  const input = document.getElementById(inputId);
  if (!container || !input) return;
  let val = 0;
  container.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      val = parseInt(btn.dataset.star);
      input.value = val;
      updateStars(container, val);
    });
    btn.addEventListener('mouseenter', () => updateStars(container, parseInt(btn.dataset.star)));
    btn.addEventListener('mouseleave', () => updateStars(container, val));
  });
}

function updateStars(container, n) {
  container.querySelectorAll('button').forEach(btn => {
    btn.classList.toggle('filled', parseInt(btn.dataset.star) <= n);
  });
}

/* ── Image Upload Preview ─────────────── */
let selectedFiles = [];

function initImageUpload(dropzoneId, inputId, previewId, counterId, minImages) {
  const dropzone = document.getElementById(dropzoneId);
  const input    = document.getElementById(inputId);
  const preview  = document.getElementById(previewId);
  const counter  = document.getElementById(counterId);
  if (!dropzone || !input) return;

  dropzone.addEventListener('click', () => input.click());
  dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    handleFiles([...e.dataTransfer.files]);
  });
  input.addEventListener('change', () => handleFiles([...input.files]));

  function handleFiles(files) {
    const valid = files.filter(f => ['image/jpeg','image/png','image/webp'].includes(f.type));
    selectedFiles = [...selectedFiles, ...valid].slice(0, 10); // max 10
    renderPreviews();
  }

  function renderPreviews() {
    if (!preview) return;
    preview.innerHTML = '';
    selectedFiles.forEach((file, i) => {
      const url   = URL.createObjectURL(file);
      const item  = document.createElement('div');
      item.className = 'preview-item' + (i === 0 ? ' primary' : '');
      item.innerHTML = `
        <img src="${url}" alt="">
        ${i === 0 ? '<div class="preview-label">Primary</div>' : ''}
        <button type="button" class="preview-remove" onclick="removeImage(${i})">×</button>
      `;
      preview.appendChild(item);
    });
    // Update the real file input via DataTransfer
    const dt = new DataTransfer();
    selectedFiles.forEach(f => dt.items.add(f));
    input.files = dt.files;
    // Update counter
    if (counter) {
      const ok = selectedFiles.length >= minImages;
      counter.className = 'img-counter ' + (ok ? 'ok' : 'warn');
      counter.textContent = selectedFiles.length < minImages
        ? `${selectedFiles.length}/${minImages} images (need ${minImages - selectedFiles.length} more)`
        : `✓ ${selectedFiles.length} image${selectedFiles.length > 1 ? 's' : ''} selected`;
    }
  }
  renderPreviews();
}

function removeImage(index) {
  selectedFiles.splice(index, 1);
  // Re-trigger render
  const event = new Event('_rerender');
  document.dispatchEvent(event);
}

document.addEventListener('_rerender', () => {
  // Find active upload init and re-render
  const preview = document.getElementById('img-preview');
  const counter = document.getElementById('img-counter');
  const input   = document.getElementById('room-images');
  if (!preview || !input) return;
  preview.innerHTML = '';
  selectedFiles.forEach((file, i) => {
    const url  = URL.createObjectURL(file);
    const item = document.createElement('div');
    item.className = 'preview-item' + (i === 0 ? ' primary' : '');
    item.innerHTML = `
      <img src="${url}">
      ${i === 0 ? '<div class="preview-label">Primary</div>' : ''}
      <button type="button" class="preview-remove" onclick="removeImage(${i})">×</button>
    `;
    preview.appendChild(item);
  });
  const dt = new DataTransfer();
  selectedFiles.forEach(f => dt.items.add(f));
  input.files = dt.files;
  if (counter) {
    const ok = selectedFiles.length >= 4;
    counter.className = 'img-counter ' + (ok ? 'ok' : 'warn');
    counter.textContent = selectedFiles.length < 4
      ? `${selectedFiles.length}/4 images (need ${4 - selectedFiles.length} more)`
      : `✓ ${selectedFiles.length} image${selectedFiles.length > 1 ? 's' : ''} selected`;
  }
});

/* ── Geolocation / Nearby ─────────────── */
function getNearbyRooms() {
  const btn = document.getElementById('nearby-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '📍 Locating... <span class="spinner"></span>'; }

  navigator.geolocation.getCurrentPosition(
    pos => {
      const { latitude, longitude } = pos.coords;
      fetch(`/api/nearby?lat=${latitude}&lng=${longitude}`)
        .then(r => r.json())
        .then(rooms => {
          renderNearbyPanel(rooms, latitude, longitude);
          if (btn) { btn.disabled = false; btn.innerHTML = '📍 Rooms Near Me'; }
        })
        .catch(() => {
          showToast('Could not load nearby rooms');
          if (btn) { btn.disabled = false; btn.innerHTML = '📍 Rooms Near Me'; }
        });
    },
    err => {
      showToast('Please allow location access');
      if (btn) { btn.disabled = false; btn.innerHTML = '📍 Rooms Near Me'; }
    },
    { timeout: 8000 }
  );
}

function renderNearbyPanel(rooms, lat, lng) {
  const panel = document.getElementById('nearby-panel');
  if (!panel) return;
  if (!rooms.length) {
    panel.innerHTML = '<p style="color:var(--muted);font-size:14px">No rooms found near your location yet. Be the first to add one!</p>';
    panel.classList.add('show');
    return;
  }
  panel.innerHTML = `
    <h4>📍 Rooms Near You</h4>
    <div class="nearby-list">
      ${rooms.map(r => `
        <a class="nearby-card" href="/room/${r.id}">
          ${r.image
            ? `<img src="/static/uploads/${r.image}" alt="${r.title}">`
            : `<div style="width:100%;height:100px;background:#f0ede8;display:flex;align-items:center;justify-content:center;font-size:28px">🏠</div>`
          }
          <div class="nc-body">
            <div class="nc-title">${r.title}</div>
            <div class="nc-meta">${r.location}</div>
            <div class="nc-price">₹${r.rent.toLocaleString()}/mo</div>
            <div class="nc-dist">📍 ${r.distance_km} km away</div>
          </div>
        </a>`).join('')}
    </div>`;
  panel.classList.add('show');
}

/* ── Get location for Add Room form ───── */
function getFormLocation() {
  const btn = document.getElementById('get-loc-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '📍 Getting location...'; }

  navigator.geolocation.getCurrentPosition(
    pos => {
      const { latitude, longitude } = pos.coords;
      document.getElementById('lat-input').value  = latitude;
      document.getElementById('lng-input').value  = longitude;
      // Reverse geocode with Nominatim (free, no API key needed)
      fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
        .then(r => r.json())
        .then(data => {
          const addr = data.address;
          const loc  = [addr.suburb || addr.neighbourhood, addr.city || addr.town, addr.state].filter(Boolean).join(', ');
          const locInput = document.getElementById('location-input');
          if (locInput && !locInput.value) locInput.value = loc;
          showToast('✅ Location captured!');
        })
        .catch(() => showToast('✅ Coordinates saved'));
      if (btn) { btn.disabled = false; btn.innerHTML = '✅ Location Captured'; }
    },
    () => {
      showToast('Location access denied');
      if (btn) { btn.disabled = false; btn.innerHTML = '📍 Use My Location'; }
    },
    { timeout: 8000 }
  );
}

/* ── Availability toggle (dashboard) ─── */
function toggleAvailability(roomId, checkbox) {
  fetch(`/toggle_availability/${roomId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      showToast(data.available ? 'Room marked as available' : 'Room marked as unavailable');
    });
}

/* ── Form validation ──────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const addForm = document.getElementById('add-room-form');
  if (addForm) {
    addForm.addEventListener('submit', e => {
      const imgInput = document.getElementById('room-images');
      if (!imgInput || imgInput.files.length < 4) {
        e.preventDefault();
        showToast('⚠️ Please upload at least 4 room images');
        document.getElementById('img-dropzone')?.scrollIntoView({ behavior: 'smooth' });
        return;
      }
      const btn = addForm.querySelector('.submit-btn');
      if (btn) { btn.disabled = true; btn.innerHTML = 'Submitting... <span class="spinner"></span>'; }
    });
  }

  // Auth tab switch
  const tabs = document.querySelectorAll('.auth-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.mode;
      window.location = mode === 'login' ? '/login' : '/register';
    });
  });
});
