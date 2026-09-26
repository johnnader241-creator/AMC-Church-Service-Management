document.addEventListener('DOMContentLoaded',()=>{
  const btn=document.getElementById('menuBtn');
  const sidebar=document.getElementById('sidebar');
  if(btn && sidebar) btn.addEventListener('click',()=>sidebar.classList.toggle('open'));

  const themeToggle=document.getElementById('themeToggle');
  const applyTheme=(dark)=>{
    document.body.classList.toggle('dark-mode', dark);
    if(themeToggle) themeToggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
    localStorage.setItem('service-theme', dark ? 'dark' : 'light');
  };
  const savedTheme=localStorage.getItem('service-theme');
  applyTheme(savedTheme === 'dark');
  if(themeToggle) themeToggle.addEventListener('click',()=>applyTheme(!document.body.classList.contains('dark-mode')));

  document.querySelectorAll('[data-toggle-password]').forEach(b=>b.addEventListener('click',()=>{const i=document.getElementById(b.dataset.togglePassword); if(i) i.type=i.type==='password'?'text':'password';}));
  document.querySelectorAll('[data-table-filter]').forEach(inp=>{const id=inp.dataset.tableFilter; const t=document.getElementById(id); if(!t)return; inp.addEventListener('input',()=>{const q=inp.value.trim().toLowerCase(); t.querySelectorAll('tbody tr').forEach(tr=>tr.style.display=tr.innerText.toLowerCase().includes(q)?'':'none');});});
  document.querySelectorAll('.donut').forEach(el=>{const txt=el.querySelector('span')?.innerText||'0'; el.style.setProperty('--value',parseFloat(txt)||0);});
  if('serviceWorker' in navigator) navigator.serviceWorker.register('/static/sw.js').catch(()=>{});
});
