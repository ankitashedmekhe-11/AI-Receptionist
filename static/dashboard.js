/* ────────────────────────────────────────────────────────────────────
   AI Receptionist — Dashboard JS
   Handles: data fetching, routing, rendering, booking, rescheduling, drawer
──────────────────────────────────────────────────────────────────── */

const apiEndpoint      = '/dashboard/data';
const autoRefreshInterval = 60; // seconds

// ── DOM refs ──────────────────────────────────────────────────────────
const receptionStatus      = document.getElementById('reception-status');
const receptionDescription = document.getElementById('reception-description');
const liveDot              = document.getElementById('live-dot');
const todayCount           = document.getElementById('today-count');
const callsCount           = document.getElementById('calls-count');
const missedCallsCount     = document.getElementById('missed-calls-count');
const lastUpdated          = document.getElementById('last-updated');
const recentCaller         = document.getElementById('recent-caller');
const recentIntent         = document.getElementById('recent-intent');
const recentResolution     = document.getElementById('recent-resolution');
const recentTranscript     = document.getElementById('recent-transcript');
const activityItems        = document.getElementById('activity-items');
const attentionList        = document.getElementById('attention-list');
const recentCallsEl        = document.getElementById('recent-calls');
const upcomingSchedule     = document.getElementById('upcoming-schedule');
const customerList         = document.getElementById('customer-list');
const statusBreakdown      = document.getElementById('status-breakdown');
const intentBreakdown      = document.getElementById('intent-breakdown');
const topServices          = document.getElementById('top-services');
const refreshButton        = document.getElementById('refresh-button');
const searchInput          = document.getElementById('search-input');
const drawer               = document.getElementById('call-detail-drawer');
const drawerClose          = document.getElementById('drawer-close');
const drawerCallerName     = document.getElementById('drawer-caller-name');
const drawerCallerPhone    = document.getElementById('drawer-caller-phone');
const drawerIntent         = document.getElementById('drawer-intent');
const drawerResolution     = document.getElementById('drawer-resolution');
const drawerTranscript     = document.getElementById('drawer-transcript');
const drawerCallLabel      = document.getElementById('drawer-call-label');
const drawerBookForm       = document.getElementById('drawer-book-form');
const drawerBookCustomer   = document.getElementById('drawer-book-customer');
const drawerBookService    = document.getElementById('drawer-book-service');
const drawerBookDate       = document.getElementById('drawer-book-date');
const drawerBookTime       = document.getElementById('drawer-book-time');
const drawerBookStatus     = document.getElementById('drawer-book-status');
const drawerBookSection    = document.getElementById('drawer-book-section');
const bookApptForm         = document.getElementById('book-appt-form');
const bookCustomerSel      = document.getElementById('book-customer');
const bookStatus           = document.getElementById('book-status');

// ── State ─────────────────────────────────────────────────────────────
let state = {
  recentCalls: [],
  customers: [],
  upcomingAppointments: [],
};

// ── Helpers ───────────────────────────────────────────────────────────
const formatTime = (value) => {
  if (!value) return '—';
  const d = new Date();
  const [h, m] = String(value).split(':');
  if (isNaN(+h) || isNaN(+m)) return value;
  d.setHours(+h, +m);
  return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
};

const formatDate = (value) => {
  if (!value) return '—';
  const d = new Date(value + 'T00:00:00');
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
};

const formatDateTime = (value) => {
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
};

const toTitleCase = (v) =>
  v ? v.toString().replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown';

const today = () => new Date().toISOString().split('T')[0];

// Detect if a call intends to book an appointment
const isBookingIntent = (call) =>
  ['book', 'appointment', 'schedule'].some(kw =>
    (call.intent || '').toLowerCase().includes(kw) ||
    (call.transcript || '').toLowerCase().includes(kw)
  );

// Extract service hint from transcript — now more generic
const extractService = (transcript = '') => {
  // No hardcoded services — just return empty and let the AI handle it
  return '';
};


// ── Reception status ──────────────────────────────────────────────────
const setReceptionState = (status) => {
  receptionStatus.textContent = toTitleCase(status);
  receptionStatus.className   = `status-pill status-${status}`;
  if (status === 'listening') {
    receptionDescription.textContent = 'Listening for incoming calls.';
    liveDot.style.background = '#10B981';
  } else if (status === 'idle') {
    receptionDescription.textContent = 'No active call. Ready for the next request.';
    liveDot.style.background = '#F59E0B';
  } else {
    receptionDescription.textContent = 'Receptionist offline. Check system status.';
    liveDot.style.background = '#EF4444';
  }
};

// ── Activity feed (Overview) ──────────────────────────────────────────
const renderActivity = (calls) => {
  if (!calls.length) {
    activityItems.innerHTML = '<li class="feed-empty">Waiting for call activity.</li>';
    recentCaller.textContent    = '—';
    recentIntent.textContent    = '—';
    recentResolution.textContent = '—';
    recentTranscript.textContent = '—';
    return;
  }
  const latest = calls.find(c => c.intent && c.intent !== null) || calls[0];
  activityItems.innerHTML = [
    `Call received at ${formatDateTime(latest.timestamp)}`,
    `Intent: ${toTitleCase(latest.intent || 'unknown')}`,
    `Action: ${latest.resolution || 'Pending'}`,
  ].map(l => `<li>${l}</li>`).join('');

  recentCaller.textContent     = latest.customer_name || '— Unknown caller';
  recentIntent.textContent     = toTitleCase(latest.intent || 'unknown');
  recentResolution.textContent = latest.resolution || 'Pending';
  recentTranscript.textContent = latest.transcript || 'No transcript available.';
};

// ── Attention panel (Overview) ────────────────────────────────────────
const renderAttention = (data) => {
  const items = [];
  if (data.missed_calls > 0)
    items.push({ title: `${data.missed_calls} missed call${data.missed_calls > 1 ? 's' : ''}`, msg: 'Follow up with callers who were not answered.' });
  if ((data.appointments_by_status?.pending || 0) > 0)
    items.push({ title: `${data.appointments_by_status.pending} pending request(s)`, msg: 'Confirm or reschedule these appointments.' });
  if ((data.appointments_by_status?.cancelled || 0) > 0)
    items.push({ title: `${data.appointments_by_status.cancelled} cancelled booking(s)`, msg: 'Consider reaching out to affected customers.' });

  // Calls awaiting booking confirmation
  const bookingPending = (data.recent_calls || []).filter(c => isBookingIntent(c) && (!c.resolution || c.resolution === 'Pending'));
  if (bookingPending.length > 0)
    items.push({ title: `${bookingPending.length} call${bookingPending.length > 1 ? 's' : ''} need booking confirmation`, msg: 'Go to Calls and click each to confirm the appointment.' });

  if (!items.length) {
    attentionList.innerHTML = '<li class="feed-empty">No items require attention right now.</li>';
    return;
  }
  attentionList.innerHTML = items.map(i => `
    <li class="attention-item">
      <strong>${i.title}</strong>
      <span>${i.msg}</span>
    </li>
  `).join('');
};

// ── Recent calls (Calls section) ──────────────────────────────────────
const renderRecentCalls = (calls, query = '') => {
  const filtered = calls.filter(c => {
    const q = query.toLowerCase();
    return !q || c.customer_name?.toLowerCase().includes(q)
               || c.intent?.toLowerCase().includes(q)
               || c.transcript?.toLowerCase().includes(q);
  });

  if (!filtered.length) {
    recentCallsEl.innerHTML = '<div class="feed-empty">No calls match the search.</div>';
    return;
  }

  recentCallsEl.innerHTML = filtered.map((call, i) => {
    const needsBooking = isBookingIntent(call) && (!call.resolution || call.resolution === 'Pending');
    const isIncomplete = !call.intent || call.intent === 'unknown' || call.intent === null;
    const callerDisplay = call.customer_name || '\u2014';
    const intentDisplay = isIncomplete ? 'Incomplete' : toTitleCase(call.intent);
    return `
      <div class="call-row${needsBooking ? ' call-row--needs-booking' : ''}" data-call-index="${i}">
        <div class="call-intent">
          <span class="call-badge${isIncomplete ? ' call-badge--incomplete' : ''}">${intentDisplay}</span>
          <span class="row-meta">${formatDateTime(call.timestamp)}</span>
          ${needsBooking ? '<span class="booking-alert-badge">⚡ Needs Booking</span>' : ''}
          ${isIncomplete ? '<span style="font-size:0.75rem; color: var(--text-muted); background: rgba(255,255,255,0.05); border-radius:6px; padding:2px 7px; margin-left:4px;">incomplete</span>' : ''}
        </div>
        <p class="call-summary">${call.transcript ? call.transcript.slice(0, 160) : 'No transcript available.'}</p>
        <div class="call-row-footer">
          <p class="row-meta">Outcome: ${call.resolution || (isIncomplete ? '\u2014' : 'Pending')} \xB7 ${callerDisplay}</p>
          ${needsBooking ? `<button class="confirm-book-btn" data-index="${i}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Confirm Booking
          </button>` : ''}
        </div>
      </div>
    `;
  }).join('');

  recentCallsEl.querySelectorAll('.call-row').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('.confirm-book-btn')) return; // handled below
      openCallDrawer(filtered[+row.dataset.callIndex]);
    });
  });

  recentCallsEl.querySelectorAll('.confirm-book-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openCallDrawer(filtered[+btn.dataset.index], true);
    });
  });
};

// ── Upcoming schedule with Reschedule (Appointments section) ──────────
const renderUpcomingSchedule = (appointments) => {
  if (!appointments.length) {
    upcomingSchedule.innerHTML = '<div class="feed-empty">No upcoming appointments scheduled.</div>';
    return;
  }

  upcomingSchedule.innerHTML = appointments.map(a => `
    <div class="schedule-item" id="appt-item-${a.id}">
      <div class="schedule-item-time">${formatTime(a.time)}</div>
      <div class="schedule-item-body">
        <p class="schedule-item-title">${a.service}</p>
        <p class="schedule-item-meta">${a.customer_name || `Customer #${a.customer_id}`} · ${formatDate(a.date)}</p>
      </div>
      <div class="schedule-item-actions">
        <span class="appt-status appt-status--${a.status}">${toTitleCase(a.status)}</span>
        <button class="reschedule-btn" data-appt-id="${a.id}" data-service="${a.service}" data-date="${a.date}" data-time="${a.time}" title="Reschedule">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Reschedule
        </button>
        ${a.status !== 'cancelled' ? `<button class="cancel-btn" data-appt-id="${a.id}" title="Cancel">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>` : ''}
      </div>
    </div>
    <!-- Inline reschedule form (hidden by default) -->
    <div class="reschedule-form-wrap hidden" id="reschedule-form-${a.id}">
      <form class="reschedule-form" data-appt-id="${a.id}">
        <div class="field-group" style="margin:0">
          <label>Service</label>
          <input type="text" name="service" value="${a.service}" required />
        </div>
        <div class="field-group" style="margin:0">
          <label>Date</label>
          <input type="date" name="date" value="${a.date}" required />
        </div>
        <div class="field-group" style="margin:0">
          <label>Time</label>
          <input type="time" name="time" value="${a.time.substring(0,5)}" required />
        </div>
        <div class="reschedule-actions">
          <button type="submit" class="primary-button" style="padding:9px 18px;font-size:0.85rem">Save</button>
          <button type="button" class="secondary-button cancel-reschedule-btn" data-appt-id="${a.id}" style="padding:9px 18px;font-size:0.85rem;background:var(--bg)">Discard</button>
          <span class="reschedule-status field-note"></span>
        </div>
      </form>
    </div>
  `).join('');

  // Attach reschedule toggle
  upcomingSchedule.querySelectorAll('.reschedule-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.apptId;
      const form = document.getElementById(`reschedule-form-${id}`);
      form.classList.toggle('hidden');
    });
  });

  // Discard reschedule
  upcomingSchedule.querySelectorAll('.cancel-reschedule-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById(`reschedule-form-${btn.dataset.apptId}`)?.classList.add('hidden');
    });
  });

  // Submit reschedule
  upcomingSchedule.querySelectorAll('.reschedule-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = form.dataset.apptId;
      const status = form.querySelector('.reschedule-status');
      status.textContent = 'Saving…';
      status.style.color = 'var(--text-muted)';

      const payload = {
        service: form.elements.service.value.trim(),
        date: form.elements.date.value,
        time: form.elements.time.value + ':00',
      };

      try {
        const res = await fetch(`/appointments/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to reschedule');
        }
        status.textContent = '✓ Rescheduled!';
        status.style.color = '#10B981';
        setTimeout(async () => {
          document.getElementById(`reschedule-form-${id}`)?.classList.add('hidden');
          await loadDashboard();
        }, 800);
      } catch (err) {
        status.textContent = err.message;
        status.style.color = '#E11D48';
      }
    });
  });

  // Cancel appointment
  upcomingSchedule.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Cancel this appointment?')) return;
      try {
        const res = await fetch(`/appointments/${btn.dataset.apptId}/cancel`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to cancel');
        await loadDashboard();
      } catch (err) {
        alert(err.message);
      }
    });
  });
};

// ── Customers ─────────────────────────────────────────────────────────
const renderCustomers = (customers, query = '') => {
  const filtered = customers.filter(c => {
    const q = query.toLowerCase();
    return !q || c.name?.toLowerCase().includes(q)
               || c.phone?.toLowerCase().includes(q)
               || c.latest_intent?.toLowerCase().includes(q);
  });

  if (!filtered.length) {
    customerList.innerHTML = '<div class="feed-empty">No customers match the search.</div>';
    return;
  }

  customerList.innerHTML = filtered.map(c => `
    <div class="customer-card">
      <div class="customer-avatar">${(c.name || '?')[0].toUpperCase()}</div>
      <div class="customer-info">
        <p class="customer-name">${c.name}</p>
        <p class="customer-meta">${c.phone || 'No phone'} · ${c.total_calls} call${c.total_calls !== 1 ? 's' : ''} · ${c.total_appointments} appt${c.total_appointments !== 1 ? 's' : ''}</p>
        <p class="customer-meta">${c.last_interaction ? 'Last contact: ' + formatDateTime(c.last_interaction) : 'No interaction yet'}</p>
      </div>
      <span class="call-badge">${toTitleCase(c.latest_intent || 'none')}</span>
    </div>
  `).join('');
};

// ── Analytics ─────────────────────────────────────────────────────────
const renderBreakdown = (el, data) => {
  if (!Object.keys(data).length) { el.innerHTML = '<li class="feed-empty">No data yet.</li>'; return; }
  const max = Math.max(...Object.values(data));
  el.innerHTML = Object.entries(data).sort(([, a], [, b]) => b - a).map(([label, count]) => {
    const pct = max > 0 ? Math.round((count / max) * 100) : 0;
    return `<li class="insight-bar-item">
      <div class="insight-bar-top"><span>${toTitleCase(label)}</span><strong>${count}</strong></div>
      <div class="insight-bar-track"><div class="insight-bar-fill" style="width:${pct}%"></div></div>
    </li>`;
  }).join('');
};

const renderTopServices = (services) => {
  if (!services.length) { topServices.innerHTML = '<li class="feed-empty">No service data yet.</li>'; return; }
  const max = services[0].count;
  topServices.innerHTML = services.map((s, i) => {
    const pct = max > 0 ? Math.round((s.count / max) * 100) : 0;
    return `<li class="insight-bar-item">
      <div class="insight-bar-top"><span>${s.service}</span><strong>#${i + 1} · ${s.count}</strong></div>
      <div class="insight-bar-track"><div class="insight-bar-fill" style="width:${pct}%"></div></div>
    </li>`;
  }).join('');
};

// ── Customer dropdowns ────────────────────────────────────────────────
const populateCustomerDropdowns = (customers) => {
  const opts = customers.map(c => `<option value="${c.id}">${c.name}${c.phone ? ' · ' + c.phone : ''}</option>`).join('');
  [bookCustomerSel, drawerBookCustomer].forEach(sel => {
    if (sel) sel.innerHTML = '<option value="">Select customer…</option>' + opts;
  });
};

// ── Call drawer ───────────────────────────────────────────────────────
const openCallDrawer = (call, forceBooking = false) => {
  drawerCallerName.textContent  = call.customer_name || 'Unknown caller';
  drawerCallerPhone.textContent = call.customer_id ? `Customer ID ${call.customer_id}` : 'No customer linked';
  drawerIntent.textContent      = toTitleCase(call.intent);
  drawerResolution.textContent  = call.resolution || 'Pending';
  drawerTranscript.textContent  = call.transcript || 'No transcript available.';
  drawerCallLabel.textContent   = `Call at ${formatDateTime(call.timestamp)}`;

  // Show or hide the booking form
  const showBooking = forceBooking || isBookingIntent(call);
  if (drawerBookSection) {
    drawerBookSection.classList.toggle('hidden', !showBooking);
  }

  // Pre-fill form
  if (showBooking) {
    if (call.customer_id) drawerBookCustomer.value = String(call.customer_id);
    drawerBookService.value = extractService(call.transcript);
    drawerBookDate.value    = today();
    drawerBookTime.value    = '09:00';
    drawerBookStatus.textContent = '';

    // Update header label to make intent clear
    const h = drawerBookSection?.querySelector('.d-book-header span');
    if (h) {
      h.textContent = isBookingIntent(call)
        ? 'Confirm Appointment Booking'
        : 'Book Appointment';
    }
  }

  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
};

const closeDrawer = () => {
  drawer.classList.remove('open');
  drawer.setAttribute('aria-hidden', 'true');
};

// ── Drawer booking form submit ─────────────────────────────────────────
drawerBookForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const customerId = drawerBookCustomer.value;
  const service    = drawerBookService.value.trim();
  const date       = drawerBookDate.value;
  const time       = drawerBookTime.value;

  if (!customerId || !service || !date || !time) {
    drawerBookStatus.textContent = 'Please fill all fields.';
    drawerBookStatus.style.color = '#E11D48';
    return;
  }
  drawerBookStatus.textContent = 'Booking…';
  drawerBookStatus.style.color = 'var(--text-muted)';

  try {
    const res = await fetch('/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: +customerId, service, date, time }),
    });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
    drawerBookStatus.textContent = '✓ Appointment booked! Check the Appointments tab.';
    drawerBookStatus.style.color = '#10B981';
    drawerBookForm.reset();
    await loadDashboard();
  } catch (err) {
    drawerBookStatus.textContent = err.message;
    drawerBookStatus.style.color = '#E11D48';
  }
});

// ── Appointments page form submit ─────────────────────────────────────
bookApptForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const customerId = bookCustomerSel.value;
  const service    = document.getElementById('book-service').value.trim();
  const date       = document.getElementById('book-date').value;
  const time       = document.getElementById('book-time').value;

  if (!customerId || !service || !date || !time) {
    bookStatus.textContent = 'Please fill all fields.';
    bookStatus.style.color = '#E11D48';
    return;
  }
  bookStatus.textContent = 'Booking…';
  bookStatus.style.color = 'var(--text-muted)';

  try {
    const res = await fetch('/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: +customerId, service, date, time }),
    });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
    bookStatus.textContent = '✓ Appointment confirmed!';
    bookStatus.style.color = '#10B981';
    bookApptForm.reset();
    await loadDashboard();
  } catch (err) {
    bookStatus.textContent = err.message;
    bookStatus.style.color = '#E11D48';
  }
});

// ══ SPA ROUTER ════════════════════════════════════════════════════════
const sections = {
  overview:     'section-overview',
  calls:        'section-calls',
  appointments: 'section-appointments',
  customers:    'section-customers',
  analytics:    'section-analytics',
};

const pageTitles = {
  overview:     ['Command Center', 'AI-powered reception dashboard'],
  calls:        ['Calls', 'Recent call log — click any row to inspect'],
  appointments: ['Appointments', 'Schedule & manage bookings'],
  customers:    ['Customers', 'Caller profiles sorted by activity'],
  analytics:    ['Analytics', 'Performance breakdown'],
};

const navigateTo = (path) => {
  let route = (path || '/overview').replace(/^\//, '').split('#')[0] || 'overview';
  if (route === 'dashboard' || route === '') route = 'overview';
  if (!sections[route]) route = 'overview';

  Object.values(sections).forEach(id => document.getElementById(id)?.classList.add('hidden'));
  document.getElementById(sections[route])?.classList.remove('hidden');

  document.querySelectorAll('.nav-item[data-route]').forEach(link => {
    const href = (link.getAttribute('href') || '').replace(/^\//, '') || 'overview';
    const r = href === 'dashboard' ? 'overview' : href;
    link.classList.toggle('active', r === route);
  });

  const [title, sub] = pageTitles[route] || pageTitles.overview;
  document.querySelector('.page-title').textContent = title;
  document.querySelector('.page-sub').textContent   = sub;
};

document.querySelectorAll('a[data-route]').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const href = link.getAttribute('href');
    window.history.pushState({}, '', href);
    navigateTo(href);
  });
});
window.addEventListener('popstate', () => navigateTo(window.location.pathname));

// ── Search ────────────────────────────────────────────────────────────
searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim();
  renderRecentCalls(state.recentCalls, q);
  renderCustomers(state.customers, q);
});
window.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement !== searchInput) {
    e.preventDefault();
    searchInput.focus();
  }
});

// ── Data load ─────────────────────────────────────────────────────────
const loadDashboard = async () => {
  try {
    const res = await fetch(apiEndpoint);
    if (!res.ok) throw new Error('Failed to load data.');
    const data = await res.json();

    state.recentCalls          = data.recent_calls || [];
    state.customers            = data.customers || [];
    state.upcomingAppointments = data.upcoming_appointments || [];

    // Overview
    setReceptionState(data.reception_status || 'idle');
    todayCount.textContent       = data.appointments_today ?? '0';
    callsCount.textContent       = data.recent_call_count ?? '0';
    missedCallsCount.textContent = data.missed_calls ?? '0';

    renderActivity(state.recentCalls);
    renderAttention({ ...data, recent_calls: state.recentCalls });
    renderRecentCalls(state.recentCalls, searchInput.value.trim());
    renderUpcomingSchedule(state.upcomingAppointments);
    renderCustomers(state.customers, searchInput.value.trim());
    renderBreakdown(statusBreakdown, data.appointments_by_status || {});
    renderBreakdown(intentBreakdown, data.calls_by_intent || {});
    renderTopServices(data.top_services || []);
    populateCustomerDropdowns(state.customers);

    const now = new Date();
    lastUpdated.textContent = `Updated ${now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  } catch (err) {
    lastUpdated.textContent = 'Update failed';
    console.error(err);
  }
};

// ── Init ──────────────────────────────────────────────────────────────
refreshButton.addEventListener('click', loadDashboard);
drawerClose.addEventListener('click', closeDrawer);
navigateTo(window.location.pathname);
loadDashboard();
setInterval(loadDashboard, autoRefreshInterval * 1000);
