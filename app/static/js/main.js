// - aside - //
const aside = document.getElementById('sidebar');
const asideToggleBtn = document.getElementById('toggle-aside');
const sidebarHeader = document.getElementById('sidebar-header');
let userCollapsed = false;

// Свернуть/развернуть вручную через кнопку
if (asideToggleBtn) {
  asideToggleBtn.addEventListener('click', function(e) {
    e.preventDefault();
    const full = asideToggleBtn.querySelector('.sidebar-full');
    const collapsed = asideToggleBtn.querySelector('.sidebar-collapsed');
    if (aside.classList.contains('collapsed')) {
      // Разворачиваем
      aside.classList.remove('collapsed');
      aside.style.width = '';
      userCollapsed = false;
      if (full) full.classList.add('hidden'); // Скрыть длинный текст сразу
      // Короткий текст НЕ трогаем, он скроется после transitionend
    } else {
      // Сворачиваем
      if (full && collapsed) {
        full.classList.add('hidden');
        collapsed.classList.remove('hidden');
      }
      aside.classList.add('collapsed');
      aside.style.width = '';
      userCollapsed = true;
    }
  });
}

// Показываем длинный текст и скрываем короткий только после завершения transition
aside.addEventListener('transitionend', function(e) {
  if (e.propertyName === 'width' && !aside.classList.contains('collapsed')) {
    const full = asideToggleBtn.querySelector('.sidebar-full');
    const collapsed = asideToggleBtn.querySelector('.sidebar-collapsed');
    if (full && collapsed) {
      full.classList.remove('hidden');
      collapsed.classList.add('hidden');
    }
  }
});



// - Mobile меню - //
const mobileToggle = document.getElementById('mobile-toggle');
const mobileMenu = document.getElementById('mobileMenu');
const backdrop = document.getElementById('backdrop');

// Универсальный стек окон
window.modalStack = window.modalStack || [];

function openModal(type) {
  if (!window.modalStack.includes(type)) {
    window.modalStack.push(type);
    document.body.classList.add(`${type}-open`);
    const modalEl = document.getElementById(type === 'mobile-filter' ? 'mobileFilter' : 'mobileMenu');
    if (modalEl) modalEl.classList.add('open');
    backdrop.classList.add('open');
    
    // Генерируем событие для других скриптов
    console.log('[main.js] Dispatching modalOpened event for:', type);
    window.dispatchEvent(new CustomEvent('modalOpened', { detail: { type } }));
  }
}

function closeModal(type) {
  const idx = window.modalStack.lastIndexOf(type);
  if (idx !== -1) {
    window.modalStack.splice(idx, 1);
    document.body.classList.remove(`${type}-open`);
    const modalEl = document.getElementById(type === 'mobile-filter' ? 'mobileFilter' : 'mobileMenu');
    if (modalEl) modalEl.classList.remove('open');
    if (window.modalStack.length === 0) {
      backdrop.classList.remove('open');
    }
  }
}

if (mobileToggle) mobileToggle.addEventListener('click', () => openModal('mobile-menu'));

if (backdrop) {
  backdrop.addEventListener('click', function() {
    if (window.modalStack && window.modalStack.length) {
      const topModal = window.modalStack[window.modalStack.length - 1];
      if (window.closeModal) window.closeModal(topModal);
    }
  });
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' && window.modalStack.length > 0) {
    const topModal = window.modalStack[window.modalStack.length - 1];
    if (window.closeModal) window.closeModal(topModal);
  }
});

// Экспортируем для других скриптов
window.openModal = openModal;
window.closeModal = closeModal;

