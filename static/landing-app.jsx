const { useMemo, useState } = React;

const initialForm = {
  full_name: "",
  email: "",
  phone: "",
  country: "",
  budget: "",
  interest_type: "",
  preferred_lot_or_area: "",
  message: "",
};

const interestTypes = [
  "Residential Lot Purchase",
  "Golf Membership",
  "Property Investment",
  "Schedule a Visit",
];

function validate(values) {
  const errors = {};
  if (!values.full_name.trim()) errors.full_name = "Please enter your full name.";
  if (!values.email.trim()) errors.email = "Please enter your email address.";
  else if (!/^\S+@\S+\.\S+$/.test(values.email)) errors.email = "Please enter a valid email.";
  if (!values.phone.trim()) errors.phone = "Please enter your phone or WhatsApp.";
  if (!values.country.trim()) errors.country = "Please enter your country of residence.";
  if (!values.budget.trim()) errors.budget = "Please enter your estimated budget.";
  else if (Number(values.budget) <= 0) errors.budget = "Budget must be greater than 0.";
  if (!values.interest_type.trim()) errors.interest_type = "Please select your interest type.";
  return errors;
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState({ type: "", message: "" });
  const [loading, setLoading] = useState(false);

  const hasErrors = useMemo(() => Object.keys(errors).length > 0, [errors]);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    const validationErrors = validate(form);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length > 0) {
      setStatus({ type: "error", message: "Please review the highlighted fields and try again." });
      return;
    }

    try {
      setLoading(true);
      const response = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, budget: Number(form.budget) }),
      });

      const payload = await response.json();
      if (!response.ok) {
        setStatus({ type: "error", message: payload.message || "Unable to submit form." });
        return;
      }

      setStatus({ type: "success", message: payload.message });
      setForm(initialForm);
      setErrors({});
    } catch {
      setStatus({ type: "error", message: "Connection issue. Please try again in a moment." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="hero">
        <div className="overlay"></div>
        <div className="hero-content">
          <p className="eyebrow">South Pacific, Costa Rica • Golf & Real Estate</p>
          <h1>Discover the Golf Lifestyle in Costa Rica</h1>
          <p className="subtitle">Exclusive residential lots surrounded by nature and a beautiful golf course in the South Pacific of Costa Rica.</p>
          <p className="hero-description">Osa Golf Course offers a unique opportunity to own property inside a peaceful golf community surrounded by tropical rainforest, fresh air, and natural beauty. Ideal for retirement, lifestyle, or investment.</p>
          <a href="#lead-form" className="cta-button">Request Information</a>
        </div>
      </header>

      <main className="content-wrapper">
        <section className="card">
          <h2>Why Osa Golf Course?</h2>
          <ul className="benefit-list">
            <li>Beautiful 9-hole golf course surrounded by nature</li>
            <li>Peaceful community away from crowded tourist areas</li>
            <li>Residential lots available for custom homes</li>
            <li>Located in the South Pacific of Costa Rica</li>
            <li>Ideal for retirement, vacation homes, or investment</li>
            <li>A unique lifestyle connected with nature and golf</li>
          </ul>
        </section>

        <section className="card" id="lead-form">
          <h2>Request Information About Available Lots</h2>
          <p className="section-description">Fill out the form below and our team will send you detailed information about available lots, pricing, and visiting opportunities.</p>

          <form onSubmit={onSubmit} noValidate>
            <div className="grid">
              {[
                ["full_name", "Full Name", "text"],
                ["email", "Email Address", "email"],
                ["phone", "Phone / WhatsApp", "text"],
                ["country", "Country of Residence", "text"],
                ["budget", "Estimated Budget", "number"],
              ].map(([name, label, type]) => (
                <label key={name}>
                  {label}
                  <input name={name} type={type} value={form[name]} onChange={onChange} />
                  {errors[name] && <small className="field-error">{errors[name]}</small>}
                </label>
              ))}

              <label>
                Interest Type
                <select name="interest_type" value={form.interest_type} onChange={onChange}>
                  <option value="">Select one</option>
                  {interestTypes.map((option) => <option key={option}>{option}</option>)}
                </select>
                {errors.interest_type && <small className="field-error">{errors.interest_type}</small>}
              </label>

              <label>
                Preferred Lot or Area (optional)
                <input name="preferred_lot_or_area" type="text" value={form.preferred_lot_or_area} onChange={onChange} />
              </label>
            </div>

            <label>
              Message
              <textarea name="message" rows="4" value={form.message} onChange={onChange}></textarea>
            </label>

            <button type="submit" disabled={loading}>{loading ? "Sending..." : "Request Information"}</button>
          </form>

          {status.message && (
            <div className={`feedback ${status.type === "success" ? "success" : "error"}`}>
              {status.message}
            </div>
          )}

          {hasErrors && <p className="inline-hint">Please complete all required fields correctly.</p>}
        </section>
      </main>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
