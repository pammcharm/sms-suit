document.addEventListener('DOMContentLoaded', () => {
  const counters = document.querySelectorAll('[data-counter]');
  counters.forEach((counter) => {
    const target = Number(counter.dataset.counter || 0);
    const prefix = counter.dataset.prefix || '';
    const duration = 700;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const value = target * (1 - Math.pow(1 - progress, 3));
      counter.textContent = `${prefix}${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  });
});
