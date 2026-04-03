import { initApp } from './js/main.js';

try {
  initApp();
} catch (err) {
  document.body.insertAdjacentHTML(
    'afterbegin',
    `<pre style="color:red;padding:16px;background:#fff3f3;border:2px solid red;margin:8px">JS Init Error: ${err}\n${err.stack || ''}</pre>`,
  );
  console.error('initApp error:', err);
}
