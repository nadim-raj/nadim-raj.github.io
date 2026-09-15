(function(){
  var d=document.documentElement;
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO='IntersectionObserver' in window;

  /* Theme */
  var btn=document.getElementById('theme'),meta=document.querySelector('meta[name="theme-color"]');
  function paint(t){btn.setAttribute('aria-label',t==='dark'?'Switch to light theme':'Switch to dark theme');if(meta)meta.setAttribute('content',t==='dark'?'#07070A':'#F9FAFB')}
  paint(d.getAttribute('data-theme'));
  btn.addEventListener('click',function(){var t=d.getAttribute('data-theme')==='dark'?'light':'dark';d.setAttribute('data-theme',t);try{localStorage.setItem('theme',t)}catch(e){}paint(t)});

  /* Nav state + progress */
  var nav=document.querySelector('.nav'),bar=document.querySelector('.progress'),ticking=false;
  function onScroll(){var y=window.scrollY||0,h=d.scrollHeight-window.innerHeight;nav.classList.toggle('scrolled',y>8);bar.style.transform='scaleX('+(h>0?Math.min(y/h,1):0)+')';ticking=false}
  window.addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(onScroll)}},{passive:true});
  onScroll();

  /* Reveal on scroll */
  var els=[].slice.call(document.querySelectorAll('.reveal'));
  if(hasIO&&!reduce){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -6% 0px',threshold:0.08});
    els.forEach(function(el){io.observe(el)});
  }else{els.forEach(function(el){el.classList.add('in')})}

  /* Count up */
  function count(el){var end=+el.getAttribute('data-count'),t0=null,dur=1300;el.textContent='0';
    function f(t){if(t0===null)t0=t;var p=Math.min((t-t0)/dur,1);el.textContent=Math.round(end*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(f)}
    requestAnimationFrame(f)}
  if(hasIO&&!reduce){
    var co=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){count(e.target);co.unobserve(e.target)}})},{threshold:0.6});
    [].forEach.call(document.querySelectorAll('[data-count]'),function(n){co.observe(n)});
  }

  /* Active nav link */
  var links=[].slice.call(document.querySelectorAll('.links a')),byId={};
  links.forEach(function(a){byId[a.getAttribute('href').slice(1)]=a});
  if(hasIO){
    var so=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(a){a.classList.remove('active')});if(byId[e.target.id])byId[e.target.id].classList.add('active')}})},{rootMargin:'-45% 0px -50% 0px'});
    Object.keys(byId).forEach(function(id){var s=document.getElementById(id);if(s)so.observe(s)});
  }

  /* Card spotlight */
  if(window.matchMedia&&window.matchMedia('(pointer: fine)').matches){
    [].forEach.call(document.querySelectorAll('.spot'),function(c){c.addEventListener('pointermove',function(e){var r=c.getBoundingClientRect();c.style.setProperty('--mx',(e.clientX-r.left)+'px');c.style.setProperty('--my',(e.clientY-r.top)+'px')})});
  }

  var y=document.getElementById('year');if(y)y.textContent=new Date().getFullYear();
})();

/* Email address assembled at runtime so it never appears in page source */
(function(){
  var els=document.querySelectorAll('[data-u][data-d]');if(!els.length)return;
  var addr=els[0].getAttribute('data-u')+'@'+els[0].getAttribute('data-d');
  [].forEach.call(els,function(el){el.setAttribute('href','mailto:'+el.getAttribute('data-u')+'@'+el.getAttribute('data-d'))});
  [].forEach.call(document.querySelectorAll('.js-email-text'),function(t){t.textContent=addr});
})();
