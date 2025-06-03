const aside = document.getElementById('sidebar');
const asideToggleBtn = document.getElementById('toggle-aside');
const sidebarHeader = document.getElementById('sidebar-header');
let userCollapsed = false;

// Свернуть вручную через кнопку
if (asideToggleBtn) {
  asideToggleBtn.addEventListener('click', function(e) {
    e.stopPropagation(); // Не всплывает к header
    aside.classList.add('collapsed');
    aside.style.width = '';
    userCollapsed = true;
  });
}

// Развернуть по клику на header, если свернуто
if (sidebarHeader) {
  sidebarHeader.addEventListener('click', function(e) {
    if (aside.classList.contains('collapsed')) {
      aside.classList.remove('collapsed');
      aside.style.width = '';
      userCollapsed = false;
    }
  });
}

// Автоматическое сжатие и сворачивание aside при ресайзе
function handleAsideResize() {
  if (window.innerWidth > 768) {
    if (!userCollapsed) {
      // Пропорционально сжимай, но не меньше 150px
      let newWidth = Math.max(150, Math.min(200, window.innerWidth / 6));
      aside.style.width = newWidth + 'px';
      if (newWidth <= 150) {
        aside.classList.add('collapsed');
        aside.style.width = '';
      } else {
        aside.classList.remove('collapsed');
      }
    }
  } else {
    aside.style.width = '';
    aside.classList.remove('collapsed');
    userCollapsed = false;
  }
}
window.addEventListener('resize', handleAsideResize);
window.addEventListener('DOMContentLoaded', handleAsideResize);



// Mobile меню
document.addEventListener("DOMContentLoaded", function() {
  const mobileToggle = document.getElementById('mobile-toggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const mobileBackdrop = document.getElementById('mobile-backdrop');

  function openMobileMenu() {
    document.body.classList.add('mobile-menu-open');
    if (mobileMenu) mobileMenu.classList.add('open');
    if (mobileBackdrop) mobileBackdrop.classList.add('show');
  }

  function closeMobileMenu() {
    document.body.classList.remove('mobile-menu-open');
    if (mobileMenu) mobileMenu.classList.remove('open');
    if (mobileBackdrop) mobileBackdrop.classList.remove('show');
  }

  if (mobileToggle) mobileToggle.addEventListener('click', openMobileMenu);
  if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobileMenu);
});



// Выделение строки таблицы
document.querySelectorAll('#product-table tr').forEach(row => {
  row.addEventListener('click', () => {
    document.querySelectorAll('#product-table tr').forEach(r => r.classList.remove('bg-blue-100'));
    row.classList.add('bg-blue-100');
  });
});


/** Обновить пагинацию */
function renderPagination(limit, page, total, total_pages) {
  pagDiv.innerHTML = '';
  function pageBtn(num, label, disabled = false, active = false) {
    return `<button
      class="pagination-btn ${active ? 'bg-blue-500 text-white' : 'bg-gray-200'} px-2 py-1 mx-1 rounded"
      data-page="${num}" ${disabled ? 'disabled' : ''}>
      ${label}
    </button>`;
  }
  if (page > 1) pagDiv.innerHTML += pageBtn(page - 1, '«');
  let start = Math.max(1, page - 2), end = Math.min(total_pages, page + 2);
  if (start > 1) pagDiv.innerHTML += pageBtn(1, '1') + '<span>...</span>';
  for (let i = start; i <= end; i++) pagDiv.innerHTML += pageBtn(i, i, false, i === page);
  if (end < total_pages) pagDiv.innerHTML += '<span>...</span>' + pageBtn(total_pages, total_pages);
  if (page < total_pages) pagDiv.innerHTML += pageBtn(page + 1, '»');
  pagInfo.textContent = `Показано ${Math.min((page - 1) * limit + 1, total)}-${Math.min(page * limit, total)} из ${total}`;
  pagDiv.querySelectorAll('.pagination-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      currentPage = parseInt(this.dataset.page);
      fetchPage();
    });
  });
}