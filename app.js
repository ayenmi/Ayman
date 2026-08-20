function forwardOf(el, target) {
  const now = gsap.getProperty(el, 'rotation');
  const lifted = target + 360 * Math.round((now - target) / 360);
  return lifted < now ? lifted + 360 : lifted;
}

function tick() {
  const now = new Date();
  const sec = now.getSeconds();
  const targetRotation = sec * 6;

  const secEl = document.getElementById('sec');
  const nextRotation = forwardOf(secEl, targetRotation);

  gsap.to(secEl, {
    rotation: nextRotation,
    duration: 0.2,
    ease: 'power2.out'
  });

  document.getElementById('readout').innerText = now.toTimeString().split(' ')[0];

  scheduleTick();
}

function scheduleTick() {
  gsap.delayedCall(
    (1000 - Date.now() % 1000) / 1000,
    tick
  );
}

scheduleTick();