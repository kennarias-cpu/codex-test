const { useEffect, useState } = React;

function AdminApp() {
  const [leads, setLeads] = useState([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchLeads = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (status) params.set("status", status);

    const response = await fetch(`/api/leads?${params.toString()}`);
    const payload = await response.json();
    setLeads(payload.leads || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  return (
    <main className="dashboard-container">
      <div className="dashboard-header">
        <h1>Lead Dashboard</h1>
        <a className="cta-button" href="/">Back to Landing Page</a>
      </div>

      <div className="filters">
        <label>
          Search by name or email
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. michael@example.com" />
        </label>

        <label>
          Filter by lead status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="Hot Lead">Hot Lead</option>
            <option value="Warm Lead">Warm Lead</option>
            <option value="Cold Lead">Cold Lead</option>
          </select>
        </label>

        <div className="filter-actions">
          <button type="button" onClick={fetchLeads}>Apply</button>
        </div>
      </div>

      {loading ? <p>Loading leads...</p> : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Country</th>
                <th>Budget</th>
                <th>Interest Type</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {leads.length === 0 ? (
                <tr><td colSpan="7">No leads found.</td></tr>
              ) : leads.map((lead) => (
                <tr key={lead.id}>
                  <td>{lead.full_name}</td>
                  <td>{lead.email}</td>
                  <td>{lead.country}</td>
                  <td>${Number(lead.budget).toLocaleString()}</td>
                  <td>{lead.interest_type}</td>
                  <td><span className={`badge ${lead.lead_status.split(' ')[0].toLowerCase()}`}>{lead.lead_status}</span></td>
                  <td>{lead.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("admin-root")).render(<AdminApp />);
