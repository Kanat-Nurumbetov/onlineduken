const overlay = document.querySelector('.bottom-overlay__fade');
if (!overlay) return false;
const style = window.getComputedStyle(overlay);
return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
