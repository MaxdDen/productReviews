// === CONSTANTS & DOM-ELEMENTS ===
const filterRow = document.getElementById('tab_search');
const toggleFilterBtn = document.getElementById('toggle-filter-row');
const filterHint = document.getElementById('filter-hint');
const tableProductTBody = document.getElementById('product-tbody');
const pagInfo = document.getElementById('pagination-info');
const pageLimitSelect = document.getElementById('page-limit-select');
const pagDiv = document.getElementById('pagination-controls');
const resetSortBtn = document.getElementById('reset-sort-btn');
const sortIcon = document.getElementById('sort-icon');
const newProductBtn = document.getElementById('new_product');

// SVG для дефолтной сортировки и для сброса
const defaultIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M4 6h16M4 12h16M4 18h16" /></svg>`;
const resetIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M4 4l16 16M4 20L20 4" /></svg>`;

// Твоя дефолтная сортировка
const defaultSortBy = 'id';
const defaultSortDir = 'asc';

const filterInputs = [
  'tab_search_name', 'tab_search_ean', 'tab_search_upc', 'tab_search_brand', 'tab_search_category'
].map(id => document.getElementById(id));

// === GLOBAL STATE ===
/** @type {string} */
let sortBy = 'id';
/** @type {string} */
let sortDir = 'asc';
/** @type {number} */
let currentPage = 1;


// === UTILS ===

/** Получить значения всех фильтров */
function getFilterValues() {
  return {
    name: document.getElementById('tab_search_name').value.trim(),
    ean: document.getElementById('tab_search_ean').value.trim(),
    upc: document.getElementById('tab_search_upc').value.trim(),
    brand_id: document.getElementById('tab_search_brand').value,
    category_id: document.getElementById('tab_search_category').value,
  };
}

/** Собрать все фильтры и сортировку в объект */
function getAllFiltersAndSort() {
  const filters = {
    page: currentPage,
    limit: pageLimitSelect.value,
    sort_by: sortBy,
    sort_dir: sortDir,
    ...getFilterValues(),
  };
  // Очищаем дефолтные значения
  const defaultFilters = { page: 1, sort_by: 'id', sort_dir: 'asc', limit: 10 };
  Object.keys(filters).forEach(key => {
    if (filters[key] === '' || filters[key] === null || filters[key] === undefined) delete filters[key];
    if (filters[key] == defaultFilters[key]) delete filters[key];
  });
  return filters;
}

/** Сохраняет фильтры и сортировку в URL (history.replaceState) */ 
function updateUrlWithFilters(filters = getAllFiltersAndSort()) {
  const params = new URLSearchParams(filters).toString();
  history.replaceState(null, '', '/dashboard?' + params);
}

/** Обновить таблицу товаров */
function updateTable(data, highlightId = null) {
  tableProductTBody.innerHTML = '';
  if (!data.items || !data.items.length) {
    tableProductTBody.innerHTML = `<tr><td colspan="7" class="text-center text-gray-400">Нет товаров</td></tr>`;
    return;
  }
  data.items.forEach(product => {
    const highlightClass = (highlightId && String(product.id) === String(highlightId)) ? 'bg-yellow-100' : '';
    tableProductTBody.innerHTML += `
      <tr id="product-row-${product.id}" class="${highlightClass}">
        <td>
          <img src="${product.main_image_filename ? '/static/uploads/' + product.main_image_filename : '/static/images/placeholder.png'}"
               alt="Фото" class="w-20 h-20 object-cover rounded shadow">
        </td>
        <td>${product.name || ""}</td>
        <td>${product.ean || ""}</td>
        <td>${product.upc || ""}</td>
        <td>${product.brand ? (product.brand.name || product.brand) : ""}</td>
        <td>${product.category ? (product.category.name || product.category) : ""}</td>
        <td>
          <a href="/analyze/${product.id}/form${window.location.search ? window.location.search : ''}" class="btn btn-sm btn-outline bg-gray-300 text-white p-1 rounded hover:bg-gray-500 mr-2">Анализ</a>
          <a href="/product/${product.id}/form${window.location.search ? window.location.search : ''}" class="btn btn-sm btn-warning bg-gray-300 text-white p-1 rounded hover:bg-gray-500 mr-2">Редактировать</a>
          <button class="btn btn-sm btn-warning bg-gray-300 text-white p-1 rounded hover:bg-gray-500 mr-2 delete-btn" data-id="${product.id}">Удалить</button>
        </td>
      </tr>
    `;
  });
}


/** Запрос товаров с фильтрами и сортировкой, рендер таблицы */
function fetchPage() {
  const filters = getAllFiltersAndSort();
  const params = new URLSearchParams(filters).toString();
  fetch('/dashboard/data?' + params)
    .then(response => response.json())
    .then(data => {
      updateTable(data);
      renderPagination(data.limit, data.page, data.total, data.total_pages);
    });
  updateUrlWithFilters();
}


/** Сброс сортировки к дефолтной */
function resetSort() {
  sortBy = 'id';
  sortDir = 'asc';
  fetchPage();
}

// === EVENT LISTENERS ===

/** Удаление товара (делегирование на весь документ) */
document.addEventListener('click', async function(event) {
  if (event.target.classList.contains('delete-btn')) {
    const productId = event.target.dataset.id;
    if (!confirm('Вы уверены, что хотите удалить этот товар?')) return;
    try {
      const response = await fetch(`/product/${productId}/delete`, {
        method: 'DELETE',
        headers: { 
          "Accept": "application/json", 
          "X-CSRF-Token": getCSRFToken()
        },
      });
      if (response.ok) {
        const row = document.getElementById(`product-row-${productId}`);
        if (row) row.remove();
        // Если больше нет товаров — перейти на предыдущую страницу
        if (!tableProductTBody.querySelector('tr') || tableProductTBody.querySelectorAll('tr').length === 1 && tableProductTBody.textContent.includes('Нет товаров')) {
          if (currentPage > 1) currentPage--;
        }
        fetchPage();
      } else {
        alert('Ошибка удаления');
      }
    } catch (e) {
      alert('Ошибка соединения');
    }
  }
});

/** Пагинация/лимит на странице */
pageLimitSelect?.addEventListener('change', function() {
  currentPage = 1;
  fetchPage();
});

/** Сортировка по клику на th[data-sort] */
document.querySelectorAll('th a[data-sort]').forEach(link => {
  link.addEventListener('click', function(e) {
    e.preventDefault();
    const newSort = this.getAttribute('data-sort');
    if (sortBy === newSort) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = newSort;
      sortDir = 'asc';
    }
    updateSortBtnIcon();
    currentPage = 1;
    fetchPage();
  });
});

/** Сброс сортировки */
resetSortBtn?.addEventListener('click', function() {
  //resetSort();
  sortBy = defaultSortBy;
  sortDir = defaultSortDir;
  updateSortBtnIcon();
  fetchPage();
});

// Функция обновления кнопки
function updateSortBtnIcon() {
  if (sortBy === defaultSortBy && sortDir === defaultSortDir) {
    sortIcon.innerHTML = defaultIcon;
    resetSortBtn.title = 'Доступна сортировка';
    resetSortBtn.classList.remove('text-red-500');
  } else {
    sortIcon.innerHTML = resetIcon;
    resetSortBtn.title = 'Сбросить сортировку';
    resetSortBtn.classList.add('text-red-500');
  }
}

/** Показ/скрытие строки фильтра */
toggleFilterBtn.addEventListener('click', function(e) {
  e.preventDefault();
  const isHidden = filterRow.classList.contains('hidden');
  if (isHidden) {
    filterRow.classList.remove('hidden');
    toggleFilterBtn.textContent = 'Выкл. отбор';
    filterHint.style.display = 'inline';
    filterRow.querySelector('input')?.focus();
  } else {
    filterRow.classList.add('hidden');
    toggleFilterBtn.textContent = 'Вкл. отбор';
    filterHint.style.display = 'none';
    filterInputs.forEach(inp => { if (inp.tagName === 'SELECT') inp.selectedIndex = 0; else inp.value = '' });
    fetchPage();
  }
});

/** Отправка фильтрации при изменении любого фильтра */
filterInputs.forEach(input => {
  // Для input — фильтруем только по Enter
  if (input.tagName === "INPUT") {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        currentPage = 1;
        fetchPage();
      }
    });
  } else {
    // Для select — фильтруем по change
    input.addEventListener('change', function() {
      currentPage = 1;
      fetchPage();
    });
  }
});


// --- Выделение строки ---
tableProductTBody.addEventListener('click', function(e) {
  const tr = e.target.closest('tr');
  if (!tr) return;
  // Снимаем выделение со всех строк
  tableProductTBody.querySelectorAll('tr').forEach(row => row.classList.remove('bg-yellow-100'));
  // Выделяем выбранную
  tr.classList.add('bg-yellow-100');
});


function getActiveDashboardParams() {
  const params = new URLSearchParams(window.location.search);

  // Дефолтные значения
  const defaultPagination = { page: '1', limit: '10' };
  const defaultSort = { sort_by: 'id', sort_dir: 'asc' };

  // Ключи для фильтров (добавь свои если появятся новые)
  const filterKeys = ['name', 'ean', 'upc', 'brand_id', 'category_id'];

  let filtersActive = false;
  let paginationActive = false;
  let sortActive = false;

  // Проверка по параметрам
  params.forEach((value, key) => {
    if (filterKeys.includes(key) && value !== '') {
      filtersActive = true;
    }
    if (key in defaultPagination && value !== defaultPagination[key]) {
      paginationActive = true;
    }
    if (key in defaultSort && value !== defaultSort[key]) {
      sortActive = true;
    }
  });

  return {
    filtersActive,
    paginationActive,
    sortActive
  };
}


//////////////////////////////////////////////////////////////////////////////////////////////////////////

// --- Создание товара ---
newProductBtn.addEventListener('click', async function(event) {
  event.preventDefault();

  console.log("window.location.search ? window.location.search : '': ", window.location.search ? window.location.search : '')
  window.location.href = `/product/new/form${window.location.search ? window.location.search : ''}`;
});


function getHighlightIdFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get('highlight_id');
}


async function fetchPageAndMaybeHighlight() {
  const highlightId = getHighlightIdFromUrl();
  const filters = getAllFiltersAndSort();
  const params = new URLSearchParams(filters).toString();

  const response = await fetch('/dashboard/data?' + params);
  const data = await response.json();

  // Проверяем наличие нового продукта в выдаче
  if (highlightId) {
    const found = data.items.some(item => String(item.id) === highlightId);
    if (found) {
      updateTable(data, highlightId); // подсветить строку!
      return;
    } else {
      // Если фильтров нет - пробуем последнюю страницу
      const noFilters = Object.keys(filters).length <= 3; // только page, limit, sort*
      if (noFilters && data.total_pages && currentPage !== data.total_pages) {
        currentPage = data.total_pages;
        return fetchPageAndMaybeHighlight(); // рекурсия
      } else {
        // Фильтры есть — показать сообщение
        updateTable(data);
        alert("Новая запись не попадает под выбранные фильтры/сортировку.");
        // Можно сбросить фильтры, если нужно
      }
    }
  } else {
    updateTable(data);
  }
}

async function goToPageWithHighlight(highlightId) {
  const filters = getAllFiltersAndSort();
  filters.highlight_id = highlightId;

  // Отдельно забираем параметры для highlight-page
  const params = new URLSearchParams(filters).toString();

  // 1. Запрашиваем у бэка, на какой странице новый товар с учетом фильтров/сортировки
  const resp = await fetch(`/api/v1/products/highlight-page?${params}`);
  const data = await resp.json();

  if (data.found && data.page) {
    currentPage = data.page;
    // Добавим highlight_id к url и загружаем нужную страницу
    filters.page = data.page;
    filters.highlight_id = highlightId;
    const listParams = new URLSearchParams(filters).toString();
    history.replaceState(null, '', '/dashboard?' + listParams);
    fetchProductsAndHighlight(highlightId);
  } else {
    // Товар не попадает под фильтры, информируем пользователя
    alert("Новая запись не попадает под текущие фильтры или сортировку.");
    // Можно сбросить фильтры или остаться на текущей странице
    fetchProducts(); // Без подсветки
  }
}

// После сохранения нового товара
// goToPageWithHighlight(newProductId);




// === ИНИЦИАЛИЗАЦИЯ ===
window.addEventListener('DOMContentLoaded', () => {
  // Восстановить параметры из URL:
  const params = new URLSearchParams(window.location.search);
  const highlightId = params.get('highlight_id');

  const state = getActiveDashboardParams();
  if (state.filtersActive || state.paginationActive) {
    filterRow.classList.remove('hidden');
    toggleFilterBtn.textContent = 'Выкл. отбор';
    filterHint.style.display = 'inline';
  } else {
    filterRow.classList.add('hidden');
    toggleFilterBtn.textContent = 'Вкл. отбор';
    filterHint.style.display = 'none';
  }

  document.getElementById('tab_search_name').value = params.get('name') || '';
  document.getElementById('tab_search_ean').value = params.get('ean') || '';
  document.getElementById('tab_search_upc').value = params.get('upc') || '';
  document.getElementById('tab_search_brand').value = params.get('brand_id') || '';
  document.getElementById('tab_search_category').value = params.get('category_id') || '';
  sortBy = params.get('sort_by') || 'id';
  sortDir = params.get('sort_dir') || 'asc';
  currentPage = parseInt(params.get('page') || '1', 10);
  pageLimitSelect.value = params.get('limit') || '10';
 
  if (highlightId) {
    goToPageWithHighlight(highlightId);
  } else {
    fetchProducts();
  }
}); 
