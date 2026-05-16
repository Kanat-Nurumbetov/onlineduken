const out = {};
for (let i = 0; i < window.localStorage.length; i += 1) {
  const key = window.localStorage.key(i);
  out[key] = window.localStorage.getItem(key);
}
return out;
