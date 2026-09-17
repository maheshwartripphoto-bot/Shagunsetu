function ssToast(message){
  let el = document.getElementById('ss-toast');
  if(!el){
    el = document.createElement('div');
    el.id = 'ss-toast';
    el.className = 'ss-toast';
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(window.__ssToastTimer);
  window.__ssToastTimer = setTimeout(()=> el.classList.remove('show'), 2600);
}

async function ssCopy(text){
  try{
    await navigator.clipboard.writeText(text);
    ssToast('Link copied ✔');
  }catch(e){
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand('copy'); ta.remove();
    ssToast('Link copied ✔');
  }
}

async function ssShare(url, title){
  if(navigator.share){
    try{ await navigator.share({title: title || document.title, url}); return; }catch(e){}
  }
  ssCopy(url);
}

function ssOpenModal(id){
  document.getElementById(id).classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}
function ssCloseModal(id){
  document.getElementById(id).classList.add('hidden');
  document.body.style.overflow = '';
}
