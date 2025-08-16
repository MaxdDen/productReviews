// =====================
// === CONSTANTS =======
// =====================
const DASHBOARD_CONFIG = {
  SELECTORS: {
    NEW_PRODUCT_BTN: 'new_product',
    PRODUCT_TBODY: 'product-tbody',
    PRODUCT_CARDS: 'product-cards'
  },
  ROUTES: {
    NEW_PRODUCT: '/product/new/form',
    ANALYZE_PRODUCT: '/analyze/{id}/form',
    EDIT_PRODUCT: '/product/{id}/form'
  },
  MESSAGES: {
    NO_PRODUCTS: 'Нет товаров',
    DELETE_ERROR: 'Ошибка при удалении товара'
  }
};

// =========================
// === DASHBOARD MANAGER ===
// =========================
class DashboardManager {
  constructor() {
    this.newProductBtn = document.getElementById(DASHBOARD_CONFIG.SELECTORS.NEW_PRODUCT_BTN);
    this.tableProductTBody = document.getElementById(DASHBOARD_CONFIG.SELECTORS.PRODUCT_TBODY);
    
    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // Кнопка создания товара
    this.newProductBtn?.addEventListener('click', (event) => this.handleNewProduct(event));
    
    // Обработка удаления товаров
    this.tableProductTBody?.addEventListener('click', (event) => this.handleDeleteProduct(event));
  }

  handleNewProduct(event) {
    event.preventDefault();
    const params = new URLSearchParams(TableUtils.getAllFiltersAndSort());
    window.location.href = `${DASHBOARD_CONFIG.ROUTES.NEW_PRODUCT}?${params.toString()}`;
  }

  handleDeleteProduct(event) {
    const deleteBtn = event.target.closest('.delete-btn');
    if (!deleteBtn) return;

    const productId = deleteBtn.dataset.id;
    if (!productId || !confirm('Удалить этот товар?')) return;

    this.deleteProduct(productId);
  }

  async deleteProduct(productId) {
    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      alert('Нет CSRF токена! Невозможно удалить.');
      return;
    }

    try {
      const response = await fetch(`/api/product/${productId}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'X-CSRF-Token': csrf_token
        },
        credentials: 'same-origin'
      });

      if (response.ok) {
        TableUtils.fetchPage();
      } else {
        const errorData = await response.json().catch(() => null);
        alert(errorData?.detail || DASHBOARD_CONFIG.MESSAGES.DELETE_ERROR);
      }
    } catch (error) {
      console.error('Delete product error:', error);
      alert(DASHBOARD_CONFIG.MESSAGES.DELETE_ERROR);
    }
  }
}




// ====================
// === INIT ON LOAD ===
// ====================
function renderProductCards(products, cardsContainer) {
  if (!cardsContainer) {
    console.warn('[renderProductCards] Нет контейнера для карточек');
    return;
  }
  if (!products || !products.length) {
    cardsContainer.innerHTML = '<div class="text-center text-gray-400">Нет товаров</div>';
    return;
  }
  cardsContainer.innerHTML = '';
  
  const params = new URLSearchParams(TableUtils.getNonDefaultFiltersForUrl());
  const queryString = params.toString();
  const urlSuffix = queryString ? `?${queryString}` : '';
  
  products.forEach(product => {
    cardsContainer.innerHTML += `
      <div class="card relative bg-white rounded-xl shadow-custom p-[10px] shadow-[0px_2px_6px_0px_rgba(0,0,0,0.25)]" data-id="${product.id}">
        <div class="font-semibold text-sm leading-none tracking-normal align-middle mb-[4px] md:hidden">${product.name || ''}</div>
        <div class="bg-white rounded-xl shadow-custom flex flex-row gap-4">
          <img src="${product.main_image_filename ? '/static/uploads/' + product.main_image_filename : '/static/images/placeholder.png'}" alt="Фото" class="min-w-[140px] max-w-[160px] min-h-[140px] max-h-[160px] object-cover rounded-xl mx-auto md:mx-0" />
          <div class="flex-1 flex flex-col justify-between">
            <div class="card-wrap">
              <div class="font-semibold text-sm leading-none tracking-normal align-middle mb-[4px] hidden md:block">${product.name || ''}</div>
              <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">EAN: </span>${product.ean || ''}</div>
              <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">UPC: </span>${product.upc || ''}</div>
              <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Brand: </span>${product.brand ? (product.brand.name || product.brand) : ''}</div>
              <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Category: </span>${product.category ? (product.category.name || product.category) : ''}</div>
            </div>
            <div class="card-arrow flex justify-end">
              <svg width="14" height="8" viewBox="0 0 14 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12.8346 1.25L7.0013 6.75L6.16797 5.96429M1.16797 1.25L3.11214 3.08333" stroke="#1F2125" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
        </div>
        <div class="actions flex items-center justify-between gap-2 mt-4 md:mt-0 md:absolute md:right-4 md:bottom-4">
          <a href="/analyze/${product.id}/form${urlSuffix}" class="bg-[#A3B8F8] hover:bg-[#7B7FD1] text-white font-semibold px-[20px] py-[5px] rounded-full shadow transition text-[15px]">
            Analysis
          </a>
          <div class="flex items-center gap-2">
            <a href="/product/${product.id}/form${urlSuffix}" class="rounded-full hover:bg-gray-200 transition p-1" title="Edit">
              <svg width="24" height="24" viewBox="0 0 35 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="0.5" y="1" width="34" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                <path d="M18.9769 13.0492C18.9769 13.0492 19.0487 14.2805 20.135 15.3661C21.2212 16.4523 22.4519 16.5248 22.4519 16.5248L23.0312 15.9455C23.4921 15.4846 23.7511 14.8594 23.7511 14.2076C23.7511 13.5558 23.4921 12.9307 23.0312 12.4698C22.5704 12.0089 21.9452 11.75 21.2934 11.75C20.6416 11.75 20.0165 12.0089 19.5556 12.4698L18.9762 13.0492L17.5012 14.5242M22.4519 16.5242L19.1644 19.813L17.2262 21.7498L17.1262 21.8505C16.765 22.2111 16.5844 22.3917 16.3856 22.5467C16.151 22.7296 15.8972 22.8865 15.6287 23.0148C15.4012 23.123 15.1594 23.2036 14.675 23.3648L12.6244 24.0486M12.6244 24.0486L12.1231 24.2161C12.0063 24.2553 11.8808 24.2611 11.7609 24.2329C11.6409 24.2047 11.5312 24.1435 11.444 24.0564C11.3569 23.9693 11.2958 23.8595 11.2676 23.7396C11.2394 23.6196 11.2452 23.4942 11.2844 23.3773L11.4519 22.8761M12.6244 24.0486L11.4519 22.8761M11.4519 22.8761L12.1356 20.8255C12.2969 20.3411 12.3775 20.0992 12.4856 19.8717C12.6144 19.6021 12.7704 19.3498 12.9537 19.1148C13.1087 18.9161 13.2894 18.7355 13.65 18.3748L15.3137 16.7117" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
            </a>
            <button class="rounded-full hover:bg-red-100 transition p-1 delete-btn" title="Delete" data-id="${product.id}">
              <svg width="24" height="24" viewBox="0 0 33 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="0.5" y="1" width="32" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                <path d="M11 12.5L11.7639 24.3182C11.8002 25.0011 12.3139 25.5 12.9861 25.5H20.0139M21.4844 21.142L22 12.5" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 12.5H23H10Z" fill="#6B6397"/>
                <path d="M10 12.5H23" stroke="#6B6397" stroke-width="1.2" stroke-miterlimit="10" stroke-linecap="round"/>
                <path d="M14.2778 12.8636V11.3864C14.2775 11.2699 14.2988 11.1545 14.3406 11.0468C14.3823 10.9391 14.4437 10.8412 14.5211 10.7589C14.5986 10.6765 14.6906 10.6112 14.7918 10.5668C14.8931 10.5224 15.0016 10.4997 15.1111 10.5H17.8889C17.9984 10.4997 18.1069 10.5224 18.2082 10.5668C18.3094 10.6112 18.4014 10.6765 18.4789 10.7589C18.5563 10.8412 18.6177 10.9391 18.6594 11.0468C18.7012 11.1545 18.7225 11.2699 18.7222 11.3864V12.8636M16.5 15.2273V23.5M14 15.2273L14.2778 23.5M19 15.2273L18.7222 23.5" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    `;
  });
  // Активация карточек уже происходит в TableUtils.updateTable
}

// --- Переопределяем TableUtils.updateTable для вызова мобильной пагинации ---
// (Удалить monkey-patching, использовать afterUpdateTable) 

TableUtils.init({
  tableSelector: '#productTable',
  tbodySelector: '#product-tbody',
  filterRowSelector: '#tab_search',
  filterInputs: [
    '#tab_search_name',
    '#tab_search_ean',
    '#tab_search_upc',
    '#tab_search_brand',
    '#tab_search_category',
    '#mob_search_name',
    '#mob_search_ean',
    '#mob_search_upc',
    '#mob_brand_id',
    '#mob_category_id'
  ],
  filterKeys: ['name', 'ean', 'upc', 'brand_id', 'category_id'],
  mobileFilterInputs: ['mob_search_name', 'mob_search_ean', 'mob_search_upc', 'mob_brand_id', 'mob_category_id'],
  mobFilterIconId: 'mob-filter-icon',
  mobFilterIconActiveId: 'mob-filter-icon-active',
  mobFilterRowBtnId: 'mob-filter-row',
  mobSortNameId: 'mob_sort_name',
  mobSortingId: 'mob_sorting',
  mobileFilterApplyId: 'mobileFilterApply',
  mobileFilterBtnId: 'mobile-filter',
  sortLinksSelector: '.sort-link',
  paginationSelector: '#pagination-controls',
  pageLimitSelector: '#page-limit-button',
  resetSortBtnSelector: '#reset-sort-btn',
  sortBtnSelector: '#reset-sort-btn',
  sortIconSelector: '#toggle-sort-icon',
  sortIconActiveSelector: '#toggle-sort-icon-active',
  filterBtnSelector: '#toggle-filter-row',
  filterIconSelector: '#toggle-filter-icon',
  filterIconActiveSelector: '#toggle-filter-icon-active',
  defaultSortBy: 'id',
  defaultSortDir: 'asc',
  dataUrl: '/dashboard/data',
  renderRow: function(product) {
    const params = new URLSearchParams(TableUtils.getNonDefaultFiltersForUrl());
    const queryString = params.toString();
    const urlSuffix = queryString ? `?${queryString}` : '';
    
    return `
      <tr id="product-row-${product.id}" class=" h-[80px] align-middle border-b border-gray-200 table-row cursor-pointer">
        <td class="w-[80px] p-[5px]">
          <img src="${product.main_image_filename ? '/static/uploads/' + product.main_image_filename : '/static/images/placeholder.png'}"
               alt="Фото" class="w-16 h-16 object-cover rounded-xl shadow">
        </td>
        <td class="p-[5px] align-middle font-semibold text-gray-900 line-clamp-3">${product.name || ""}</td>
        <td class="w-[125px] p-[5px] align-middle text-gray-700">${product.ean || ""}</td>
        <td class="w-[120px] p-[5px] align-middle text-gray-700">${product.upc || ""}</td>
        <td class="w-[100px] xl:w-[150px] p-[5px] align-middle text-gray-700" title="brand">${product.brand ? (product.brand.name || product.brand) : ""}</td>
        <td class="w-[100px] xl:w-[150px] p-[5px] align-middle text-gray-700" title="category">${product.category ? (product.category.name || product.category) : ""}</td>
        <td class="w-[100px] xl:w-[220px] p-[5px] align-middle">
          <div class="flex flex-wrap xl:flex-nowrap items-center justify-center gap-[5px]">
            <a href="/analyze/${product.id}/form${urlSuffix}" class="bg-[#A3B8F8] hover:bg-[#7B7FD1] text-white font-semibold px-[20px] py-[5px] rounded-full shadow transition text-[15px]">
              Analysis
            </a>
            <div class="flex items-center justify-center gap-2">
              <a href="/product/${product.id}/form${urlSuffix}" class="rounded-full hover:bg-gray-200 transition p-1" title="Edit">
                <svg width="24" height="24" viewBox="0 0 35 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="0.5" y="1" width="34" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                  <path d="M18.9769 13.0492C18.9769 13.0492 19.0487 14.2805 20.135 15.3661C21.2212 16.4523 22.4519 16.5248 22.4519 16.5248L23.0312 15.9455C23.4921 15.4846 23.7511 14.8594 23.7511 14.2076C23.7511 13.5558 23.4921 12.9307 23.0312 12.4698C22.5704 12.0089 21.9452 11.75 21.2934 11.75C20.6416 11.75 20.0165 12.0089 19.5556 12.4698L18.9762 13.0492L17.5012 14.5242M22.4519 16.5242L19.1644 19.813L17.2262 21.7498L17.1262 21.8505C16.765 22.2111 16.5844 22.3917 16.3856 22.5467C16.151 22.7296 15.8972 22.8865 15.6287 23.0148C15.4012 23.123 15.1594 23.2036 14.675 23.3648L12.6244 24.0486M12.6244 24.0486L12.1231 24.2161C12.0063 24.2553 11.8808 24.2611 11.7609 24.2329C11.6409 24.2047 11.5312 24.1435 11.444 24.0564C11.3569 23.9693 11.2958 23.8595 11.2676 23.7396C11.2394 23.6196 11.2452 23.4942 11.2844 23.3773L11.4519 22.8761M12.6244 24.0486L11.4519 22.8761M11.4519 22.8761L12.1356 20.8255C12.2969 20.3411 12.3775 20.0992 12.4856 19.8717C12.6144 19.6021 12.7704 19.3498 12.9537 19.1148C13.1087 18.9161 13.2894 18.7355 13.65 18.3748L15.3137 16.7117" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </a>
              <button class="rounded-full hover:bg-red-100 transition p-1 delete-btn" title="Delete" data-id="${product.id}">
                <svg width="24" height="24" viewBox="0 0 33 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="0.5" y="1" width="32" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                  <path d="M11 12.5L11.7639 24.3182C11.8002 25.0011 12.3139 25.5 12.9861 25.5H20.0139M21.4844 21.142L22 12.5" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M10 12.5H23H10Z" fill="#6B6397"/>
                  <path d="M10 12.5H23" stroke="#6B6397" stroke-width="1.2" stroke-miterlimit="10" stroke-linecap="round"/>
                  <path d="M14.2778 12.8636V11.3864C14.2775 11.2699 14.2988 11.1545 14.3406 11.0468C14.3823 10.9391 14.4437 10.8412 14.5211 10.7589C14.5986 10.6765 14.6906 10.6112 14.7918 10.5668C14.8931 10.5224 15.0016 10.4997 15.1111 10.5H17.8889C17.9984 10.4997 18.1069 10.5224 18.2082 10.5668C18.3094 10.6112 18.4014 10.6765 18.4789 10.7589C18.5563 10.8412 18.6177 10.9391 18.6594 11.0468C18.7012 11.1545 18.7225 11.2699 18.7222 11.3864V12.8636M16.5 15.2273V23.5M14 15.2273L14.2778 23.5M19 15.2273L18.7222 23.5" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </td>
      </tr>
    `;
  },
  renderCards: renderProductCards,
  cardsContainerSelector: '#product-cards',
  defaultFilters: {
    sort_by: 'id',
    sort_dir: 'asc',
    tab_search_name: '',
    tab_search_ean: '',
    tab_search_upc: '',
    tab_search_brand: '',
    tab_search_category: ''
  },
  afterUpdateTable: function(data) {
    const params = new URLSearchParams(window.location.search);
    const highlightId = params.get('highlight_id');
    const newCreated = params.get('new_created');
    let found = false;
  
    console.log('[highlight]', { highlightId, newCreated });
  
    if (highlightId) {
      const row = document.getElementById(`product-row-${highlightId}`);
      const card = document.querySelector(`#product-cards .card[data-id='${highlightId}']`);
      console.log('[highlight] row:', row, 'card:', card);
  
      if (row) {
        found = true;
        row.classList.add('row-selected', 'row-highlight-animate');
        row.scrollIntoView({behavior: 'smooth', block: 'center'});
        setTimeout(() => row.classList.remove('row-highlight-animate'), 2000);
      }
      if (card) {
        found = true;
        card.classList.add('active', 'card-highlight-animate');
        card.scrollIntoView({behavior: 'smooth', block: 'center'});
        setTimeout(() => card.classList.remove('card-highlight-animate'), 2000);
      }
      console.log('[highlight] found:', found);
    }
  
    if (newCreated && highlightId && !found) {
      console.log('[highlight] showToast fired!');
      TableUtils.showToast('Созданный товар не соответствует текущим фильтрам. Измените фильтры, чтобы увидеть его.');
    }
  }
});


// Dropdown для лимита на странице теперь в table-utils.js

// ====================
// === INITIALIZATION ===
// ====================
document.addEventListener('DOMContentLoaded', () => {
  new DashboardManager();
});



// Adaptive //
// - Mobile Filter - //
// Мобильная логика теперь в table-utils.js


// Логика активации карточек теперь в table-utils.js




// - HELPs - //
const toggleHelpBtn = document.getElementById('toggle-help');
const toggleTooltip = document.getElementById('toggle-tooltip');

const tableActionsHelpBtn = document.getElementById('table-actions-help');
const tableActionsTooltip = document.getElementById('table-actions-tooltip');

// Основная подсказка
toggleHelpBtn.addEventListener('click', function(e) {
  e.preventDefault();
  toggleTooltip.classList.toggle('hidden');
  tableActionsTooltip.classList.add('hidden'); // скрыть вторую, если вдруг открыта
});

// Подсказка для Actions
tableActionsHelpBtn.addEventListener('click', function(e) {
  e.preventDefault();
  tableActionsTooltip.classList.toggle('hidden');
  toggleTooltip.classList.add('hidden'); // скрыть первую, если вдруг открыта
});

// Скрывать обе при клике вне
document.addEventListener('click', function(e) {
  if (
    !toggleHelpBtn.contains(e.target) && !toggleTooltip.contains(e.target) &&
    !tableActionsHelpBtn.contains(e.target) && !tableActionsTooltip.contains(e.target)
  ) {
    toggleTooltip.classList.add('hidden');
    tableActionsTooltip.classList.add('hidden');
  }
});







// Toast уведомления теперь в table-utils.js






