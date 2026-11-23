document.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('input[type=date]').forEach(el=>{if(!el.min)el.min=new Date().toISOString().slice(0,10)});});
