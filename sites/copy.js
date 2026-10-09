for (const block of document.querySelectorAll('pre')) {
  const button = document.createElement('button');
  button.className = 'copy';
  button.textContent = document.documentElement.lang === 'es' ? 'Copiar' : 'Copy';
  button.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(block.textContent); }
    catch { button.textContent = document.documentElement.lang === 'es' ? 'Selecciona el código' : 'Select code to copy'; }
  });
  block.before(button);
}
