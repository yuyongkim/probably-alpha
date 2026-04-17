(() => {
  const buttons = Array.from(document.querySelectorAll('.back-to-top'));
  if (!buttons.length) {
    return;
  }

  const thresholdFor = (button) => {
    const raw = button.dataset.scrollThreshold || button.getAttribute('data-scroll-threshold') || '400';
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : 400;
  };

  const update = () => {
    const scrollY = window.scrollY || window.pageYOffset || 0;
    buttons.forEach((button) => {
      button.classList.toggle('is-visible', scrollY > thresholdFor(button));
    });
  };

  window.addEventListener('scroll', update, { passive: true });
  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
  update();
})();
