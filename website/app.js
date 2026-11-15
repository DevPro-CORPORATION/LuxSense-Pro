document.addEventListener('DOMContentLoaded', () => {
  // 1. Interactive Simulator Engine
  const luxSlider = document.getElementById('lux-slider');
  const luxValEl = document.getElementById('sim-lux-val');
  const fcValEl = document.getElementById('fc-val');
  const irrValEl = document.getElementById('irradiance-val');
  const uncValEl = document.getElementById('uncertainty-val');
  const presetBtns = document.querySelectorAll('.btn-preset');

  function updateSimulator(lux) {
    luxValEl.textContent = `${lux.toFixed(2)} lx`;

    // 1 FC = 10.7639104 lx
    const fc = lux / 10.7639104;
    fcValEl.textContent = `${fc.toFixed(2)} fc`;

    // Equivalent Irradiance at peak photopic 555nm (1 W/m² = 683 lx)
    const irradiance = lux / 683.002;
    irrValEl.textContent = `${irradiance.toFixed(4)} W/m²`;

    // Expanded Uncertainty (k=2.0, 95% Confidence)
    // Type B tolerance ~4%, ADC quantization, noise
    const uB = (0.04 * lux) / Math.sqrt(3);
    const uA = Math.max(0.05, 0.005 * lux);
    const uc = Math.sqrt(uA * uA + uB * uB);
    const U95 = 2.0 * uc;
    uncValEl.textContent = `±${U95.toFixed(2)} lx`;
  }

  if (luxSlider) {
    luxSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value);
      updateSimulator(val);
      presetBtns.forEach(btn => btn.classList.remove('active'));
    });
  }

  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      presetBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const val = parseFloat(btn.getAttribute('data-val'));
      if (luxSlider) luxSlider.value = val;
      updateSimulator(val);
    });
  });

  // Initial update
  updateSimulator(500.0);

  // 2. Documentation Tabs
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add('active');
    });
  });

  // 3. Click to Copy SHA-256 Hashes
  const hashes = document.querySelectorAll('.checksum-hash');
  hashes.forEach(hashEl => {
    hashEl.addEventListener('click', () => {
      const text = hashEl.textContent.trim();
      navigator.clipboard.writeText(text).then(() => {
        const origTitle = hashEl.title;
        hashEl.style.borderColor = '#21D789';
        hashEl.style.color = '#21D789';
        hashEl.textContent = 'COPIED TO CLIPBOARD!';
        setTimeout(() => {
          hashEl.textContent = text;
          hashEl.style.borderColor = '';
          hashEl.style.color = '';
        }, 1500);
      }).catch(err => {
        console.error('Failed to copy hash: ', err);
      });
    });
  });
});
