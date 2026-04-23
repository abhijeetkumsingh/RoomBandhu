/* ═══════════════════════════════════════════════════════════
   RoomBandhu — main.js  (mobile-first, CSRF-safe)
   ═══════════════════════════════════════════════════════════ */

'use strict';

/* ── CSRF token ──────────────────────────────────────────── */
function csrf() {
  const m = document.querySelector('meta[name="csrf-token"]');
  return m ? m.getAttribute('content') : '';
}

/* ── post helper ─────────────────────────────────────────── */
function post(url) {
  return fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' }
  });
}

/* ── Navbar scroll shadow ────────────────────────────────── */
const _nav = document.getElementById('navbar');
if (_nav) {
  window.addEventListener('scroll', () => {
    _nav.classList.toggle('scrolled', window.scrollY > 8);
  }, { passive: true });
}

/* ── Hamburger menu ──────────────────────────────────────── */
function toggleMenu() {
  const links = document.getElementById('nav-links');
  const ham   = document.getElementById('hamburger');
  links && links.classList.toggle('open');
  ham   && ham.classList.toggle('open');
}

/* Close menu on outside click */
document.addEventListener('click', e => {
  const links = document.getElementById('nav-links');
  const ham   = document.getElementById('hamburger');
  if (links && links.classList.contains('open') &&
      !links.contains(e.target) && !ham.contains(e.target)) {
    links.classList.remove('open');
    ham && ham.classList.remove('open');
  }
});

/* ── User dropdown ───────────────────────────────────────── */
function toggleUserMenu() {
  document.getElementById('user-dropdown')?.classList.toggle('show');
}
document.addEventListener('click', e => {
  const dd = document.getElementById('user-dropdown');
  if (dd && !e.target.closest('.user-menu')) dd.classList.remove('show');
});

/* ── Flash auto-dismiss ──────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .35s, transform .35s';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(() => el.remove(), 380);
    }, 4200);
  });
});

/* ── Wishlist toggle ─────────────────────────────────────── */
function toggleWish(btn, roomId) {
  post(`/wishlist/toggle/${roomId}`)
    .then(r => r.json())
    .then(data => {
      btn.textContent = data.saved ? '❤️' : '🤍';
      btn.classList.toggle('active', data.saved);

      const badge = document.getElementById('wish-badge');
      if (badge) badge.textContent = data.count;

      // On wishlist page — animate out removed card
      if (!data.saved && window.location.pathname === '/wishlist') {
        const card = btn.closest('.room-card');
        if (card) {
          card.style.transition = 'opacity .3s, transform .3s';
          card.style.opacity = '0';
          card.style.transform = 'scale(.94)';
          setTimeout(() => card.remove(), 320);
        }
      }
    })
    .catch(err => console.warn('Wishlist error:', err));
}

/* ── Availability toggle (dashboard) ────────────────────── */
function toggleAvailability(roomId, checkbox) {
  post(`/toggle_availability/${roomId}`)
    .then(r => r.json())
    .then(data => {
      const row   = checkbox.closest('.my-room-row');
      const label = row ? row.querySelector('.avail-label') : null;
      if (label) label.textContent = data.available ? 'Live' : 'Hidden';
    })
    .catch(() => { checkbox.checked = !checkbox.checked; }); // revert on error
}

/* ── Nearby rooms ────────────────────────────────────────── */
function getNearbyRooms() {
  const btn = document.getElementById('nearby-btn');
  if (!navigator.geolocation) { alert('Geolocation not supported by your browser.'); return; }

  if (btn) { btn.textContent = '📍 Getting location…'; btn.disabled = true; }

  navigator.geolocation.getCurrentPosition(
    pos => {
      const { latitude, longitude } = pos.coords;
      fetch(`/api/nearby?lat=${latitude}&lng=${longitude}`)
        .then(r => r.json())
        .then(rooms => {
          renderNearby(rooms);
          if (btn) { btn.textContent = '📍 Rooms Near Me'; btn.disabled = false; }
        })
        .catch(() => {
          if (btn) { btn.textContent = '📍 Rooms Near Me'; btn.disabled = false; }
        });
    },
    () => {
      alert('Could not get your location. Please allow location access and try again.');
      if (btn) { btn.textContent = '📍 Rooms Near Me'; btn.disabled = false; }
    },
    { timeout: 8000 }
  );
}

function renderNearby(rooms) {
  const panel = document.getElementById('nearby-panel');
  if (!panel) return;
  if (!rooms.length) {
    panel.innerHTML = '<p style="color:var(--muted);padding:12px 0;font-size:14px">No nearby rooms found with GPS coordinates.</p>';
    return;
  }
  panel.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
      <h3 style="font-family:var(--fh);font-size:17px;font-weight:700">📍 Rooms Near You</h3>
      <button onclick="document.getElementById('nearby-panel').innerHTML=''"
              style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--muted);line-height:1">×</button>
    </div>
    <div class="rooms-grid">
      ${rooms.map(r => `
        <div class="room-card" style="cursor:pointer" onclick="location.href='/room/${r.id}'">
          <div class="card-img">
            ${r.image
              ? `<img src="/static/uploads/${r.image}" alt="${r.title}" loading="lazy">`
              : `<div class="img-placeholder">🏠</div>`}
            <div class="card-badges"><span class="badge badge-type">${r.type}</span></div>
          </div>
          <div class="card-body">
            <div class="card-title">${r.title}</div>
            <div class="card-loc">📍 ${r.location}</div>
            <div class="card-price">₹${r.rent.toLocaleString('en-IN')}<small>/month</small></div>
            <div style="font-size:12px;color:var(--muted);margin-top:4px">
              📏 ${r.distance_km} km away · ⭐ ${r.rating}
            </div>
          </div>
        </div>`).join('')}
    </div>`;
}

/* ── GPS capture for add-room form ──────────────────────── */
function getFormLocation() {
  const btn = document.getElementById('get-loc-btn');
  if (!navigator.geolocation) { alert('Geolocation not supported.'); return; }
  if (btn) { btn.textContent = '📍 Locating…'; btn.disabled = true; }

  navigator.geolocation.getCurrentPosition(
    pos => {
      document.getElementById('lat-input').value = pos.coords.latitude.toFixed(6);
      document.getElementById('lng-input').value = pos.coords.longitude.toFixed(6);
      if (btn) {
        btn.textContent = '✅ Location captured!';
        btn.style.background = '#e6f9f1';
        btn.style.color = '#1a7a52';
        btn.style.borderColor = '#b2f0d6';
      }
    },
    () => {
      alert('Could not get location. Please try again.');
      if (btn) { btn.textContent = '📍 Use My Current Location'; btn.disabled = false; }
    },
    { timeout: 8000 }
  );
}

/* ── Image upload with drag-drop & preview ───────────────── */
function initImageUpload(dropzoneId, inputId, previewId, counterId, minImages) {
  const zone    = document.getElementById(dropzoneId);
  const input   = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  const counter = document.getElementById(counterId);
  if (!zone || !input) return;

  let files = [];

  zone.addEventListener('click',     () => input.click());
  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    addFiles([...e.dataTransfer.files]);
  });
  input.addEventListener('change', () => addFiles([...input.files]));

  function addFiles(newFiles) {
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    newFiles.forEach(f => {
      if (files.length >= 10) return;
      if (!allowed.includes(f.type)) return;
      files.push(f);
    });
    render(); sync();
  }

  function render() {
    if (!preview) return;
    preview.innerHTML = '';
    files.forEach((f, i) => {
      const reader = new FileReader();
      reader.onload = e => {
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `<img src="${e.target.result}" alt="">
          <button type="button" onclick="__rb_removeImg(${i})" class="remove-img">×</button>
          ${i === 0 ? '<span class="cover-label">Cover</span>' : ''}`;
        preview.appendChild(div);
      };
      reader.readAsDataURL(f);
    });
    updateCounter();
  }

  function updateCounter() {
    if (!counter) return;
    const need = Math.max(0, minImages - files.length);
    counter.textContent = need > 0
      ? `${files.length}/${minImages} photos (need ${need} more)`
      : `${files.length} photos selected ✅`;
    counter.className = 'img-counter ' + (need > 0 ? 'warn' : 'ok');
  }

  function sync() {
    try {
      const dt = new DataTransfer();
      files.forEach(f => dt.items.add(f));
      input.files = dt.files;
    } catch(e) {} // DataTransfer not available in all envs
  }

  window.__rb_removeImg = i => { files.splice(i, 1); render(); sync(); };
}
