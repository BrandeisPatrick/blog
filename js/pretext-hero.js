// Pretext-powered hero tagline.
// Uses @chenglou/pretext to measure each word with the Canvas API (no DOM
// reflow), then "freely arranges" the words — left-to-right but with a little
// rotation + vertical jitter so it reads like hand-placed type.
//
// Progressive enhancement: if this script (or the CDN) fails to load, the
// element keeps its plain, fully-readable text. Nothing breaks.

import { prepareWithSegments, layoutWithLines } from 'https://esm.sh/@chenglou/pretext@0.0.7';

const el = document.getElementById('pretext-hero');
if (el) {
  const original = el.dataset.text || el.textContent.trim();

  // A concrete font string is required for Canvas measurement; build it from
  // the element's own computed style so layout matches what the browser paints.
  function fontString() {
    const cs = getComputedStyle(el);
    return `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  }
  function fontSizePx() {
    return parseFloat(getComputedStyle(el).fontSize) || 22;
  }

  function measure(word, font, lineHeight) {
    const prepared = prepareWithSegments(word, font);
    const { lines } = layoutWithLines(prepared, 1e6, lineHeight); // huge width -> single line
    return lines.length ? lines[0].width : 0;
  }

  function arrange() {
    const font = fontString();
    const size = fontSizePx();
    const lh = size * 1.45;
    const maxW = el.clientWidth;
    const space = measure('x x', font, lh) - 2 * measure('x', font, lh); // real space width

    const words = original.split(/\s+/).filter(Boolean);
    el.textContent = '';
    el.classList.add('pretext-ready');

    let x = 0, line = 0;
    let i = 0;
    for (const word of words) {
      const w = measure(word, font, lh);
      if (x > 0 && x + w > maxW) { x = 0; line++; } // wrap using measured width

      const span = document.createElement('span');
      span.className = 'px-word';
      span.textContent = word;
      const rot = (Math.random() * 7 - 3.5).toFixed(2);     // -3.5deg..3.5deg
      const jitter = (Math.random() * 10 - 5).toFixed(1);   // -5px..5px
      span.style.setProperty('--rot', `${rot}deg`);
      span.style.setProperty('--delay', `${i * 0.06}s`);
      span.style.left = `${x}px`;
      span.style.top = `${line * lh + parseFloat(jitter)}px`;
      el.appendChild(span);

      x += w + space;
      i++;
    }

    el.style.height = `${(line + 1) * lh + 14}px`;

    // Trigger the staggered fade/slide-in on the next frame.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.querySelectorAll('.px-word').forEach((s) => s.classList.add('in'));
      });
    });
  }

  function run() {
    try {
      arrange();
    } catch (err) {
      console.error('[pretext-hero] falling back to plain text:', err);
      el.classList.remove('pretext-ready');
      el.removeAttribute('style');
      el.textContent = original;
    }
  }

  // Wait for fonts so measurement matches the painted glyphs.
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(run);

  // Re-arrange on resize (debounced) so wrapping stays correct on rotation/resize.
  let t;
  window.addEventListener('resize', () => {
    clearTimeout(t);
    t = setTimeout(run, 150);
  });
}
