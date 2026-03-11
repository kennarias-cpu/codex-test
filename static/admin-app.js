const root = document.getElementById('admin-app');

root.innerHTML = `
  <main class="dashboard-container">
    <div class="dashboard-header">
      <h1>Lead Dashboard</h1>
      <a class="cta-button" href="/">Back to Landing Page</a>
    </div>

    <div class="filters">
      <label>Search by name or email
        <input id="search" placeholder="e.g. michael@example.com" />
      </label>
      <label>Filter by lead status
        <select id="status">
          <option value="">All statuses</option>
          <option value="Hot Lead">Hot Lead</option>
          <option value="Warm Lead">Warm Lead</option>
          <option value="Cold Lead">Cold Lead</option>
        </select>
      </label>
      <div class="filter-actions"><button id="applyFilters">Apply</button></div>
    </div>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>Country</th><th>Budget</th><th>Interest Type</th><th>Status</th><th>Date</th>
          </tr>
        </thead>
        <tbody id="leadsBody"><tr><td colspan="7">Loading...</td></tr></tbody>
      </table>
    </div>
  </main>
`;

const bodyEl = document.getElementById('leadsBody');

async function loadLeads() {
  const q = document.getElementById('search').value.trim();
  const status = document.getElementById('status').value;
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (status) params.set('status', status);

  bodyEl.innerHTML = '<tr><td colspan="7">Loading...</td></tr>';
  const response = await fetch(`/api/leads?${params.toString()}`);
  const payload = await response.json();
  const leads = payload.leads || [];

  if (!leads.length) {
    bodyEl.innerHTML = '<tr><td colspan="7">No leads found.</td></tr>';
    return;
  }

  bodyEl.innerHTML = leads.map((lead) => `
    <tr>
      <td>${escapeHtml(lead.full_name)}</td>
      <td>${escapeHtml(lead.email)}</td>
      <td>${escapeHtml(lead.country)}</td>
      <td>$${Number(lead.budget).toLocaleString()}</td>
      <td>${escapeHtml(lead.interest_type)}</td>
      <td><span class="badge ${lead.lead_status.split(' ')[0].toLowerCase()}">${escapeHtml(lead.lead_status)}</span></td>
      <td>${escapeHtml(lead.created_at)}</td>
    </tr>
  `).join('');
}

function escapeHtml(value) {
  return String(value || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

document.getElementById('applyFilters').addEventListener('click', loadLeads);
loadLeads();
