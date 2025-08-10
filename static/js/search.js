// Global Search with voice and live suggestions
(function () {
  const input = document.getElementById('globalSearchInput');
  const list = document.getElementById('searchSuggestions');
  const voiceBtn = document.getElementById('voiceSearchBtn');
  if (!input || !list) return;

  let controller;
  input.addEventListener('input', async function () {
    const q = input.value.trim();
    if (controller) controller.abort();
    if (!q) { list.innerHTML = ''; return; }
    try {
      controller = new AbortController();
      const res = await fetch(`/api/search_suggestions?q=${encodeURIComponent(q)}`, { signal: controller.signal });
      const suggestions = await res.json();
      list.innerHTML = suggestions.map(s => `<a class="list-group-item list-group-item-action" href="/items?search=${encodeURIComponent(s.name)}">${s.name}</a>`).join('');
    } catch (e) { /* ignore aborted */ }
  });

  document.addEventListener('click', () => { list.innerHTML = ''; });
  list.addEventListener('click', (e) => { e.stopPropagation(); });

  if (voiceBtn && (window.SpeechRecognition || window.webkitSpeechRecognition)) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = 'en-IN';
    rec.onresult = (ev) => {
      input.value = ev.results[0][0].transcript;
      input.form && input.form.submit();
    };
    voiceBtn.addEventListener('click', () => rec.start());
  } else if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
      alert('Voice search is not supported by your browser. Please use Chrome or Edge, or allow microphone permissions.');
    });
  }
})();

// Simple AI Assistant: routes text to search page
(function () {
  const modal = document.getElementById('aiAssistantModal');
  if (!modal) return;
  const btn = document.getElementById('aiAssistantSearchBtn');
  const field = document.getElementById('aiQuery');
  const result = document.getElementById('aiAssistantResult');
  btn.addEventListener('click', function () {
    const q = (field.value || '').trim();
    if (!q) { result.innerHTML = '<div class="text-danger">Please enter a request.</div>'; return; }
    // naive parse: forward to search page
    window.location.href = `/items?search=${encodeURIComponent(q)}`;
  });
})();

