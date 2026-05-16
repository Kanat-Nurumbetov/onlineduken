const overlay = document.querySelector('.bottom-overlay.bottom-overlay_visible');
if (!overlay) return false;
const style = window.getComputedStyle(overlay);
return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
