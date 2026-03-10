const form = document.getElementById('prospectForm');
const feedback = document.getElementById('feedback');

form?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  try {
    const response = await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    feedback.className = response.ok ? 'feedback success' : 'feedback error';
    feedback.textContent = result.message;

    if (response.ok) {
      form.reset();
    }
  } catch (error) {
    feedback.className = 'feedback error';
    feedback.textContent = 'Unable to submit your request right now. Please try again shortly.';
  }
});
