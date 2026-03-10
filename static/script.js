const form = document.getElementById('prospectForm');
const feedback = document.getElementById('feedback');
const registrationDateField = document.querySelector('input[name="registration_date"]');

if (registrationDateField && !registrationDateField.value) {
  registrationDateField.value = new Date().toISOString().slice(0, 10);
}

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

    if (response.ok && result.classification) {
      feedback.textContent = `${result.message} Priority status: ${result.classification}.`;
      form.reset();
      if (registrationDateField) {
        registrationDateField.value = new Date().toISOString().slice(0, 10);
      }
    } else {
      feedback.textContent = result.message;
    }
  } catch (error) {
    feedback.className = 'feedback error';
    feedback.textContent = 'Unable to submit your request right now. Please try again shortly.';
  }
});
