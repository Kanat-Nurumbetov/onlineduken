const overlay = document.querySelector('.bottom-overlay.bottom-overlay_visible');
if (!overlay) return '';
const candidates = Array.from(
  overlay.querySelectorAll(
    '.user-addresses__item, .user-addresses__item-inner, [class*="address"], [class*="store"], [class*="item"]'
  )
);
for (const candidate of candidates) {
  const rect = candidate.getBoundingClientRect();
  const text = (candidate.innerText || candidate.textContent || '').trim();
  if (!text || !rect.width || !rect.height) continue;
  candidate.scrollIntoView({block: 'center'});
  candidate.click();
  return text;
}
return '';
