(function(){
  const rtl = new Set(['ar']);
  const key = 'vita-lang';
  
const base = location.origin.startsWith("http") ? "/i18n" : "../i18n"; // because pages live under /html
  let dict = {};

  async function j(p){ const r = await fetch(p); if(!r.ok) throw new Error('i18n fetch '+p); return r.json(); }

  async function merge(lang, namespaces){
    const common = await j(`${base}/${lang}/common.json`);
    const out = {...common};
    for(const ns of namespaces){ Object.assign(out, await j(`${base}/${lang}/${ns}.json`)); }
    return out;
  }

  async function load(lang, namespaces){
    const primary = await merge(lang, namespaces);
    if(lang==='en'){ dict = primary; }
    else {
      const fb = await merge('en', namespaces);
      dict = new Proxy(primary, { get:(o,k)=> (k in o ? o[k] : fb[k]) });
    }
    localStorage.setItem(key, lang);
    document.documentElement.lang = lang;
    document.documentElement.dir  = rtl.has(lang) ? 'rtl' : 'ltr';
  }

  function t(k, params={}){
    let s = dict[k] ?? k;
    for(const [kk,v] of Object.entries(params)){ s = s.replace(new RegExp(`{${kk}}`,'g'), v); }
    return s;
  }

  function apply(){
    document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.getAttribute('data-i18n')));
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => el.placeholder = t(el.getAttribute('data-i18n-placeholder')));
    document.querySelectorAll('[data-i18n-value]').forEach(el => el.value = t(el.getAttribute('data-i18n-value')));
  }

  async function init(namespaces=[]){ await load(localStorage.getItem(key)||'en', namespaces); apply(); }
  async function switchLang(lang, namespaces=[]){ await load(lang, namespaces); apply(); }

  window.I18N = { init, switchLang, t };
})();
