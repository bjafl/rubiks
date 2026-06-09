export function initLibrary({ onLoadAlg, onAnimateSeq }) {
  fetch('/api/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'get_library' }),
  })
    .then(r => r.json())
    .then(data => {
      if (!data.library) return;
      const list = document.getElementById('alg-list');
      for (const { name } of data.library) {
        const el = document.createElement('div');
        el.className = 'alg-item';
        el.textContent = name;
        el.dataset.name = name;
        el.addEventListener('click', () => {
          document.querySelectorAll('.alg-item').forEach(e => e.classList.remove('active'));
          el.classList.add('active');
          onLoadAlg(name);
        });
        list.appendChild(el);
      }
    });

  document.getElementById('seq-submit').addEventListener('click', () => {
    const seq = document.getElementById('seq-input').value.trim();
    if (!seq) return;
    document.querySelectorAll('.alg-item').forEach(e => e.classList.remove('active'));
    onAnimateSeq(seq);
  });

  document.getElementById('seq-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      document.getElementById('seq-submit').click();
    }
  });
}
