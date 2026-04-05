/* ===================================================
   VANILLE DE MADAGASCAR — script.js
   =================================================== */

/* ---------- Cart State ---------- */
let cart = [];

/* ---------- DOM refs ---------- */
const cartBadge    = document.getElementById('cart-badge');
const cartBtn      = document.getElementById('cart-btn');
const cartSidebar  = document.getElementById('cart-sidebar');
const cartOverlay  = document.getElementById('cart-overlay');
const cartClose    = document.getElementById('cart-close');
const cartItemsEl  = document.getElementById('cart-items');
const cartEmpty    = document.getElementById('cart-empty');
const cartFooter   = document.getElementById('cart-footer');
const cartTotal    = document.getElementById('cart-total');
const checkoutBtn  = document.getElementById('checkout-btn');
const cartSuccess  = document.getElementById('cart-success');
const cartShopLink = document.getElementById('cart-shop-link');
const toast        = document.getElementById('toast');
const navbar       = document.getElementById('navbar');
const hamburger    = document.getElementById('hamburger');
const navLinks     = document.getElementById('nav-links');
const contactForm  = document.getElementById('contact-form');
const formSuccess  = document.getElementById('form-success');

/* ===================================================
   CART
   =================================================== */
function addToCart(name, price) {
  const existing = cart.find(i => i.name === name);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ name, price, qty: 1 });
  }
  updateCartUI();
  showToast(`✅ ${name} ajouté au panier`);
  bumpBadge();
}

function removeFromCart(name) {
  const idx = cart.findIndex(i => i.name === name);
  if (idx === -1) return;
  if (cart[idx].qty > 1) {
    cart[idx].qty -= 1;
  } else {
    cart.splice(idx, 1);
  }
  updateCartUI();
}

function updateCartUI() {
  /* Badge count */
  const totalQty = cart.reduce((sum, i) => sum + i.qty, 0);
  cartBadge.textContent = totalQty;

  /* Cart items */
  cartItemsEl.innerHTML = '';

  if (cart.length === 0) {
    cartItemsEl.appendChild(cartEmpty);
    cartEmpty.hidden = false;
    cartFooter.hidden = true;
    cartSuccess.hidden = true;
    checkoutBtn.hidden = false;
    return;
  }

  cartEmpty.hidden = true;
  cartFooter.hidden = false;

  const icons = {
    'Gousses de Vanille Bourbon': '🌿',
    'Gousses de Vanille Premium': '✨',
    'Poudre de Vanille Pure':     '🌸',
    'Extrait de Vanille':         '💧',
    'Vanille en Poudre Bio':      '🌱',
    'Lot Découverte':             '🎁',
  };

  cart.forEach(item => {
    const el = document.createElement('div');
    el.className = 'cart-item';
    el.innerHTML = `
      <span class="cart-item-icon">${icons[item.name] || '🌿'}</span>
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-price">${item.price} € / unité</div>
      </div>
      <div class="cart-item-controls">
        <button class="cart-qty-btn" data-action="minus" data-name="${item.name}" aria-label="Diminuer">−</button>
        <span class="cart-qty">${item.qty}</span>
        <button class="cart-qty-btn" data-action="plus" data-name="${item.name}" aria-label="Augmenter">+</button>
      </div>
    `;
    cartItemsEl.appendChild(el);
  });

  /* Total */
  const total = cart.reduce((sum, i) => sum + i.price * i.qty, 0);
  cartTotal.textContent = total + ' €';
}

/* Cart qty button delegation */
cartItemsEl.addEventListener('click', e => {
  const btn = e.target.closest('.cart-qty-btn');
  if (!btn) return;
  const name   = btn.dataset.name;
  const action = btn.dataset.action;
  if (action === 'plus')  addToCart(name, cart.find(i => i.name === name).price);
  if (action === 'minus') removeFromCart(name);
});

/* Open / close sidebar */
function openCart()  {
  cartSidebar.classList.add('open');
  cartOverlay.classList.add('visible');
  cartSidebar.setAttribute('aria-hidden', 'false');
  cartOverlay.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}
function closeCart() {
  cartSidebar.classList.remove('open');
  cartOverlay.classList.remove('visible');
  cartSidebar.setAttribute('aria-hidden', 'true');
  cartOverlay.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

cartBtn.addEventListener('click', openCart);
cartClose.addEventListener('click', closeCart);
cartOverlay.addEventListener('click', closeCart);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeCart(); });

if (cartShopLink) {
  cartShopLink.addEventListener('click', () => {
    closeCart();
    document.getElementById('produits').scrollIntoView({ behavior: 'smooth' });
  });
}

/* Checkout */
checkoutBtn.addEventListener('click', () => {
  if (cart.length === 0) return;
  checkoutBtn.hidden = true;
  cartSuccess.hidden = false;
  setTimeout(() => {
    cart = [];
    updateCartUI();
    checkoutBtn.hidden = false;
    cartSuccess.hidden = true;
    closeCart();
  }, 3000);
});

/* ===================================================
   TOAST
   =================================================== */
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

/* ===================================================
   BADGE BUMP ANIMATION
   =================================================== */
function bumpBadge() {
  cartBadge.classList.remove('bump');
  void cartBadge.offsetWidth; /* reflow */
  cartBadge.classList.add('bump');
  setTimeout(() => cartBadge.classList.remove('bump'), 300);
}

/* ===================================================
   NAVBAR SCROLL
   =================================================== */
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
}, { passive: true });

/* ===================================================
   MOBILE MENU
   =================================================== */
hamburger.addEventListener('click', () => {
  const open = hamburger.classList.toggle('open');
  navLinks.classList.toggle('open', open);
  hamburger.setAttribute('aria-expanded', open);
});

/* Close mobile menu on link click */
navLinks.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navLinks.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
  });
});

/* ===================================================
   SMOOTH SCROLL
   =================================================== */
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', e => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    const offset = navbar.offsetHeight + 8;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});

/* ===================================================
   REVEAL ON SCROLL
   =================================================== */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      /* Stagger cards in a grid */
      const delay = entry.target.closest('.products-grid, .testimonials-grid')
        ? [...entry.target.parentElement.children].indexOf(entry.target) * 80
        : 0;
      setTimeout(() => entry.target.classList.add('visible'), delay);
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* ===================================================
   CONTACT FORM
   =================================================== */
function validateForm() {
  let valid = true;

  const name    = document.getElementById('name');
  const email   = document.getElementById('email');
  const message = document.getElementById('message');

  /* Reset */
  [name, email, message].forEach(el => {
    el.classList.remove('error');
    document.getElementById(el.id + '-error').textContent = '';
  });

  if (!name.value.trim()) {
    name.classList.add('error');
    document.getElementById('name-error').textContent = 'Veuillez entrer votre nom.';
    valid = false;
  }
  if (!email.value.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    email.classList.add('error');
    document.getElementById('email-error').textContent = 'Adresse email invalide.';
    valid = false;
  }
  if (!message.value.trim()) {
    message.classList.add('error');
    document.getElementById('message-error').textContent = 'Veuillez saisir un message.';
    valid = false;
  }
  return valid;
}

contactForm.addEventListener('submit', e => {
  e.preventDefault();
  if (!validateForm()) return;

  const btn = contactForm.querySelector('button[type="submit"]');
  btn.textContent = 'Envoi en cours…';
  btn.disabled = true;

  setTimeout(() => {
    contactForm.reset();
    formSuccess.hidden = false;
    btn.textContent = 'Envoyer le message';
    btn.disabled = false;
    setTimeout(() => { formSuccess.hidden = true; }, 5000);
  }, 1200);
});

/* ===================================================
   INIT
   =================================================== */
updateCartUI();
