import { initApp } from './js/main.js';

try {
  initApp();
} catch (err) {
  const pre = document.createElement('pre');
  pre.style.color = 'red';
  pre.style.padding = '16px';
  pre.style.background = '#fff3f3';
  pre.style.border = '2px solid red';
  pre.style.margin = '8px';
  pre.textContent = `JS Init Error: ${err}\n${err.stack || ''}`;
  document.body.prepend(pre);
  console.error('initApp error:', err);
}
