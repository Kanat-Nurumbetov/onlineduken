const out = {};
for (let i = 0; i < window.sessionStorage.length; i += 1) {
  const key = window.sessionStorage.key(i);
  out[key] = window.sessionStorage.getItem(key);
}
return out;
