(() => {
  window.addEventListener('error', (event) => {
    const pre = document.createElement('pre');
    pre.className = 'global-error-banner';
    pre.style.color = 'red';
    pre.style.padding = '16px';
    pre.style.background = '#fff3f3';
    pre.style.border = '2px solid red';
    pre.style.margin = '8px';
    pre.textContent = `JS Error: ${event.message}\n${event.filename || ''}:${event.lineno || ''}`;
    document.body.prepend(pre);
  });
})();
