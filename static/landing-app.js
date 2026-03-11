const app = document.getElementById('app');

app.innerHTML = `
  <header class="hero">
    <div class="overlay"></div>
    <div class="hero-content">
      <p class="eyebrow">South Pacific, Costa Rica • Golf & Real Estate</p>
      <h1>Discover the Golf Lifestyle in Costa Rica</h1>
      <p class="subtitle">Exclusive residential lots surrounded by nature and a beautiful golf course in the South Pacific of Costa Rica.</p>
      <p class="hero-description">Osa Golf Course offers a unique opportunity to own property inside a peaceful golf community surrounded by tropical rainforest, fresh air, and natural beauty. Ideal for retirement, lifestyle, or investment.</p>
      <a href="#lead-form" class="cta-button">Request Information</a>
    </div>
  </header>

  <main class="content-wrapper">
    <section class="card">
      <h2>Why Osa Golf Course?</h2>
      <ul class="benefit-list">
        <li>Beautiful 9-hole golf course surrounded by nature</li>
        <li>Peaceful community away from crowded tourist areas</li>
        <li>Residential lots available for custom homes</li>
        <li>Located in the South Pacific of Costa Rica</li>
        <li>Ideal for retirement, vacation homes, or investment</li>
        <li>A unique lifestyle connected with nature and golf</li>
      </ul>
    </section>

    <section class="card" id="lead-form">
      <h2>Request Information About Available Lots</h2>
      <p class="section-description">Fill out the form below and our team will send you detailed information about available lots, pricing, and visiting opportunities.</p>
      <form id="leadForm" novalidate>
        <div class="grid">
          ${inputField('full_name', 'Full Name')}
          ${inputField('email', 'Email Address', 'email')}
          ${inputField('phone', 'Phone / WhatsApp')}
          ${inputField('country', 'Country of Residence')}
          ${inputField('budget', 'Estimated Budget', 'number')}

          <label>Interest Type
            <select name="interest_type">
              <option value="">Select one</option>
              <option>Residential Lot Purchase</option>
              <option>Golf Membership</option>
              <option>Property Investment</option>
              <option>Schedule a Visit</option>
            </select>
            <small class="field-error" data-error="interest_type"></small>
          </label>

          ${inputField('preferred_lot_or_area', 'Preferred Lot or Area (optional)', 'text', false)}
        </div>
        <label>Message
          <textarea name="message" rows="4"></textarea>
        </label>
        <button type="submit">Request Information</button>
      </form>
      <div id="feedback"></div>
    </section>
  </main>
`;

function inputField(name, label, type = 'text', required = true) {
  return `
    <label>${label}
      <input name="${name}" type="${type}" ${required ? '' : ''} />
      <small class="field-error" data-error="${name}"></small>
    </label>
  `;
}

const form = document.getElementById('leadForm');
const feedback = document.getElementById('feedback');

function setFieldError(name, message) {
  const el = document.querySelector(`[data-error="${name}"]`);
  if (el) el.textContent = message || '';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  feedback.className = '';
  feedback.textContent = '';

  const data = Object.fromEntries(new FormData(form).entries());
  const errors = {};

  if (!data.full_name.trim()) errors.full_name = 'Please enter your full name.';
  if (!data.email.trim()) errors.email = 'Please enter your email address.';
  else if (!/^\S+@\S+\.\S+$/.test(data.email)) errors.email = 'Please enter a valid email.';
  if (!data.phone.trim()) errors.phone = 'Please enter your phone or WhatsApp.';
  if (!data.country.trim()) errors.country = 'Please enter your country of residence.';
  if (!data.budget.trim()) errors.budget = 'Please enter your estimated budget.';
  else if (Number(data.budget) <= 0) errors.budget = 'Budget must be greater than 0.';
  if (!data.interest_type.trim()) errors.interest_type = 'Please select your interest type.';

  ['full_name', 'email', 'phone', 'country', 'budget', 'interest_type'].forEach((field) => {
    setFieldError(field, errors[field] || '');
  });

  if (Object.keys(errors).length) {
    feedback.className = 'feedback error';
    feedback.textContent = 'Please review the highlighted fields and try again.';
    return;
  }

  try {
    const response = await fetch('/api/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, budget: Number(data.budget) }),
    });
    const payload = await response.json();
    feedback.className = response.ok ? 'feedback success' : 'feedback error';
    feedback.textContent = payload.message || 'Something went wrong.';
    if (response.ok) form.reset();
  } catch {
    feedback.className = 'feedback error';
    feedback.textContent = 'Connection issue. Please try again in a moment.';
  }
});
