// Универсальный модуль для фильтрации, сортировки и пагинации таблиц
// ==========================================
// === TABLE UTILS: Universal table management
// === Usage: TableUtils.init({ ...options })
// ==========================================
//
// ПРИМЕР ИСПОЛЬЗОВАНИЯ:
// ====================
// TableUtils.init({
//   dataUrl: '/api/products',
//   filterInputs: ['#search_name', '#search_brand', '#search_category'],
//   filterKeys: ['name', 'brand_id', 'category_id'],
//   renderRow: (item) => `
//     <tr class="table-row">
//       <td>${item.name}</td>
//       <td>${item.brand}</td>
//       <td>${item.category}</td>
//     </tr>
//   `,
//   renderCards: (items, container) => {
//     container.innerHTML = items.map(item => `
//       <div class="card">
//         <h3>${item.name}</h3>
//         <p>${item.brand}</p>
//       </div>
//     `).join('');
//   },
//   cardsContainerSelector: '#product-cards',
//   defaultFilters: { status: 'active' },
//   defaultSortBy: 'name',
//   defaultSortDir: 'asc'
// });
//
// ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ:
// - dataUrl: URL для получения данных
// - renderRow ИЛИ renderCards: функция рендеринга
//
// ОПЦИОНАЛЬНЫЕ ПАРАМЕТРЫ:
// - filterInputs: массив селекторов полей фильтрации
// - filterKeys: массив ключей фильтров (если не задан, берется из name/id полей)
// - cardsContainerSelector: селектор контейнера карточек для мобильной версии
// - defaultFilters: объект с дефолтными фильтрами
// - defaultSortBy: поле для сортировки по умолчанию
// - defaultSortDir: направление сортировки по умолчанию
//
// API МЕТОДЫ:
// - TableUtils.setFilters({name: 'test', sort_by: 'price'}) - применить фильтры
// - TableUtils.setPageLimit(20) - изменить лимит страниц
// - TableUtils.fetchPage() - обновить данные
// - TableUtils.destroy() - очистить ресурсы
// ==========================================

const TableUtils = (function() {
  // =====================
  // === CONSTANTS =======
  // =====================
  const TABLE_CONFIG = {
    DEFAULT_PAGE_LIMIT: 10,
    DEFAULT_SORT_DIR: 'asc',
    TOAST_DURATION: 3500,
    TOAST_FADE_DURATION: 300,
    HIGHLIGHT_DURATION: 2000,
    PAGINATION_OBSERVER_THRESHOLD: 0.5,
    CSS_CLASSES: {
      HIDDEN: 'hidden',
      ACTIVE: 'active',
      ROW_SELECTED: 'row-selected',
      ROW_HIGHLIGHT: 'row-highlight-animate',
      CARD_HIGHLIGHT: 'card-highlight-animate'
    },
    SELECTORS: {
      PAGINATION_INFO: '#pagination-info',
      MOBILE_PAGINATION_INFO: '#mobile-pagination-info',
      MOBILE_PAGINATION_CONTROLS: '#mobile-pagination-controls',
      MOBILE_PAGINATION_CONTAINER: '#mobile-pagination',
      PAGE_LIMIT_TEXT: '#page-limit-text'
    }
  };

  // =====================
  // === STATE ===========
  // =====================
  let config = {};
  let sortBy, sortDir, currentPage, lastData;
  let pageLimit = TABLE_CONFIG.DEFAULT_PAGE_LIMIT; 
  let mobilePaginationObserver = null;
  let isInitialized = false;

  // =====================
  // === ВАЛИДАЦИЯ =======
  // =====================
  function validateConfig(options) {
    const errors = [];
    
    if (!options.dataUrl) {
      errors.push('dataUrl is required');
    }
    
    if (!options.renderRow && !options.renderCards) {
      errors.push('Either renderRow or renderCards function is required');
    }
    
    if (options.renderCards && !options.cardsContainerSelector) {
      errors.push('cardsContainerSelector is required when renderCards is provided');
    }
    
    if (errors.length > 0) {
      throw new Error('TableUtils configuration errors: ' + errors.join(', '));
    }
  }

  // =====================
  // === ОЧИСТКА ========
  // =====================
  function cleanup() {
    // Отключаем observer если есть
    if (mobilePaginationObserver) {
      mobilePaginationObserver.disconnect();
      mobilePaginationObserver = null;
    }
    
    // Сбрасываем состояние
    isInitialized = false;
  }

  // =====================
  // === ИНИЦИАЛИЗАЦИЯ ===
  // =====================
  function init(options) {
    // Валидация конфигурации
    validateConfig(options);
    
    config = Object.assign({
      tableSelector: 'table',
      tbodySelector: 'tbody',
      filterRowSelector: null,
      filterInputs: [],
      filterKeys: [], // Убираем жестко заданные ключи
      sortLinksSelector: '.sort-link',
      paginationSelector: '#pagination-controls',
      resetSortBtnSelector: '#reset-sort-btn',
      sortBtnSelector: '#reset-sort-btn', 
      sortIconSelector: '#toggle-sort-icon', 
      sortIconActiveSelector: '#toggle-sort-icon-active',
      filterBtnSelector: '#toggle-filter-row', 
      filterIconSelector: '#toggle-filter-icon', 
      filterIconActiveSelector: '#toggle-filter-icon-active',
      defaultSortBy: 'id',
      defaultSortDir: 'asc',
      dataUrl: '',
      renderRow: null, 
      renderCards: null,
      cardsContainerSelector: null,
      defaultFilters: {}, 
      afterUpdateTable: null,
      mobilePaginationInfoSelector: '#mobile-pagination-info',
      mobilePaginationControlsSelector: '#mobile-pagination-controls',
      mobilePaginationContainerSelector: '#mobile-pagination',
      mobileCardsContainerSelector: '#product-cards',
      mobileFilterInputs: [],
      mobFilterIconId: 'mob-filter-icon',
      mobFilterIconActiveId: 'mob-filter-icon-active',
      mobFilterRowBtnId: 'mob-filter-row',
      mobSortingId: 'mob_sorting',
      mobSortNameId: 'mob_sort_name',
      mobileFilterApplyId: 'mobileFilterApply',
      mobileFilterBtnId: 'mobile-filter',
      cardActivationInitialized: false,
      cardDeactivationInitialized: false,
    }, options);

    sortBy = config.defaultSortBy;
    sortDir = config.defaultSortDir;
    currentPage = 1;
    lastData = undefined;
    pageLimit = config.defaultFilters?.limit || TABLE_CONFIG.DEFAULT_PAGE_LIMIT;

    // Очистка предыдущих обработчиков
    cleanup();

    // Навесить обработчики
    setupSortHandlers();
    setupFilterHandlers();
    setupPaginationHandlers();
    setupPageLimitDropdown();
    setupResetSortHandler();
    setupFilterToggleHandler();
    setupMobileHandlers();
    setupCardActivation();
    setupCardDeactivation();

    // Сохраняем пользовательский afterUpdateTable
    config._userAfterUpdateTable = config.afterUpdateTable;
    config.afterUpdateTable = null;

    // Инициализация с параметрами из URL
    restoreStateFromUrl();
    fetchPage();
    
    isInitialized = true;
  }

  // =====================
  // === ФИЛЬТРЫ =========
  // =====================
  function getFilterValues() {
    const keys = config.filterKeys || [];
    const values = {};
    
    // Если filterKeys не заданы, используем filterInputs
    if (keys.length === 0) {
      config.filterInputs.forEach(sel => {
        const el = document.querySelector(sel);
        if (el) {
          const key = el.name || el.id;
          if (key) {
            values[key] = el.value;
          }
        }
      });
    } else {
      keys.forEach(key => {
        let el = null;
        for (const sel of config.filterInputs) {
          const candidate = document.querySelector(sel);
          if (candidate && (candidate.name === key || candidate.id === key || candidate.id.endsWith('_' + key))) {
            el = candidate;
            break;
          }
        }
        if (el) {
          values[key] = el.value;
        }
      });
    }
    
    return values;
  }

  // =====================
  // === СОСТОЯНИЕ =======
  // =====================
  function getAllFiltersAndSort() {
    const filterValues = getFilterValues();
    
    // Сначала создаем объект с дефолтными значениями
    const result = {
      ...config.defaultFilters, // Всегда включаем defaultFilters
    };
    
    // Затем перезаписываем важными значениями
    result.page = currentPage;
    result.limit = pageLimit;
    result.sort_by = sortBy;
    result.sort_dir = sortDir;
    
    // Добавляем значения фильтров, избегая дублирования
    Object.keys(filterValues).forEach(key => {
      // Если параметр уже есть в defaultFilters, не перезаписываем
      if (!(key in config.defaultFilters)) {
        result[key] = filterValues[key];
      }
    });
    
    return result;
  }

  function getNonDefaultFiltersForUrl() {
    const defaults = config.defaultFilters || {};
    const allDefaults = {
      page: 1,
      limit: 10,
      sort_by: 'id',
      sort_dir: 'asc',
      ...defaults
    };
    
    const allFilters = getAllFiltersAndSort();
    const nonDefaultFilters = {};
    
    Object.keys(allFilters).forEach(key => {
      const value = allFilters[key];
      const defaultValue = allDefaults[key];
      
      // Добавляем параметр только если он отличается от дефолтного
      if (
        value != null &&
        value !== '' &&
        String(value) !== String(defaultValue)
      ) {
        nonDefaultFilters[key] = value;
      }
    });
    
    return nonDefaultFilters;
  }

  // =====================
  // === URL =============
  // =====================
  function updateUrlWithFilters(filters = getAllFiltersAndSort()) {
    const nonDefaultFilters = getNonDefaultFiltersForUrl();
    const params = new URLSearchParams();
    
    Object.keys(nonDefaultFilters).forEach(key => {
      params.append(key, nonDefaultFilters[key]);
    });
    
    history.replaceState(null, '', window.location.pathname + (params.toString() ? '?' + params.toString() : ''));
  }

  function restoreStateFromUrl() {
    const params = new URLSearchParams(window.location.search);
    
    // Восстановление сортировки
    if (params.get('sort_by')) sortBy = params.get('sort_by');
    if (params.get('sort_dir')) sortDir = params.get('sort_dir');
    
    // Восстановление пагинации
    if (params.get('page')) {
      currentPage = parseInt(params.get('page'), 10);
    } else {
      currentPage = 1; // Дефолтное значение
    }
    
    // Восстановление лимита страниц
    if (params.get('limit')) {
      const newLimit = parseInt(params.get('limit'), 10);
      pageLimit = newLimit;
      const pageLimitText = document.getElementById('page-limit-text');
      if (pageLimitText) {
        pageLimitText.textContent = `${newLimit} on page`;
      }
      // Синхронизируем мобильный селектор
      const mobileLimit = document.getElementById('mobile_limit');
      if (mobileLimit) {
        mobileLimit.value = newLimit;
      }
    } else {
      pageLimit = 10; // Дефолтное значение
      const pageLimitText = document.getElementById('page-limit-text');
      if (pageLimitText) {
        pageLimitText.textContent = `10 on page`;
      }
      // Синхронизируем мобильный селектор
      const mobileLimit = document.getElementById('mobile_limit');
      if (mobileLimit) {
        mobileLimit.value = 10;
      }
    }
    
    // Восстановление фильтров
    config.filterInputs.forEach(sel => {
      const el = document.querySelector(sel);
      if (!el) return;
      const key = el.name || el.id;
      if (params.get(key) !== null) el.value = params.get(key);
    });
  }

  // =====================
  // === ТАБЛИЦА =========
  // =====================
  function updateTable(data) {
    // Таблица (десктоп)
    const tbody = document.querySelector(config.tbodySelector);
    if (tbody) {
      tbody.innerHTML = '';
      if (!data.items || !data.items.length) {
        tbody.innerHTML = `<tr><td colspan="99" class="text-center text-gray-400">Нет данных</td></tr>`;
      } else {
        data.items.forEach(item => {
          tbody.innerHTML += config.renderRow ? config.renderRow(item) : '<tr><td>Не реализовано</td></tr>';
        });
      }
    }
    // Карточки (мобилка/планшет)
    if (config.renderCards && config.cardsContainerSelector) {
      const container = document.querySelector(config.cardsContainerSelector);
      if (container) config.renderCards(data.items, container);
    }
    setupRowHighlighting();
    
    // ВСЕГДА вызывать десктопную пагинацию
    renderPagination(data.limit, data.page, data.total, data.total_pages);
    
    // ВСЕГДА вызывать мобильную пагинацию
    afterUpdateTableMobilePagination(data);
    
    // Синхронизируем селекторы лимита
    const pageLimitText = document.getElementById('page-limit-text');
    const mobileLimit = document.getElementById('mobile_limit');
    if (pageLimitText) {
      pageLimitText.textContent = `${data.limit} on page`;
    }
    if (mobileLimit) {
      mobileLimit.value = data.limit;
    }
    
    // Обновляем URL с текущими фильтрами
    updateUrlWithFilters();
    
    // Пользовательский afterUpdateTable (если есть)
    if (typeof config._userAfterUpdateTable === 'function') {
      config._userAfterUpdateTable(data);
    }
  }

  function setupRowHighlighting() {
    const tbody = document.querySelector(config.tbodySelector);
    if (!tbody) return;
    
    // Удаляем старые обработчики
    tbody.querySelectorAll('.table-row').forEach(row => {
      row.removeEventListener('click', handleRowClick);
    });
    
    // Добавляем новые обработчики
    tbody.querySelectorAll('.table-row').forEach(row => {
      row.addEventListener('click', handleRowClick);
    });
  }

  function handleRowClick() {
    const tbody = document.querySelector(config.tbodySelector);
    if (!tbody) return;
    
    tbody.querySelectorAll('.table-row').forEach(r => {
      r.classList.remove('row-selected');
      r.classList.remove('bg-blue-100');
    });
    
    this.classList.add('row-selected');
    this.classList.add('bg-blue-100');
  }
  
  // =====================
  // === FETCH DATA ======
  // =====================
  function fetchPage() {
    const filters = getAllFiltersAndSort();
    const params = new URLSearchParams(filters).toString();
    
    fetch(config.dataUrl + '?' + params)
      .then(async r => {
        if (r.status === 401) {
          showSessionExpiredModal();
          setTimeout(() => {
            window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname + window.location.search);
          }, 2000);
          return null;
        }
        
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        }
        
        return r.json();
      })
      .then(data => {
        if (!data) return;
        lastData = data;
        updateTable(data);
        if (data.sort_by) sortBy = data.sort_by;
        if (data.sort_dir) sortDir = data.sort_dir;
        updateSortIcons();
        updateSortBtnIcon();
      })
      .catch(error => {
        console.error('TableUtils fetch error:', error);
        showToast('Ошибка загрузки данных: ' + error.message, { duration: 5000 });
        
        // Показываем сообщение об ошибке в таблице
        const tbody = document.querySelector(config.tbodySelector);
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="99" class="text-center text-red-500">Ошибка загрузки данных</td></tr>`;
        }
      });
  }

  function showSessionExpiredModal() {
    if (document.getElementById('session-expired-modal')) return;
    const modal = document.createElement('div');
    modal.id = 'session-expired-modal';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100vw';
    modal.style.height = '100vh';
    modal.style.background = 'rgba(0,0,0,0.35)';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.zIndex = '9999';
    modal.innerHTML = `
      <div style="background: white; padding: 32px 40px; border-radius: 16px; box-shadow: 0 4px 32px rgba(0,0,0,0.15); font-size: 1.2rem; text-align: center; max-width: 90vw;">
        <b>Сессия истекла</b><br><br>
        Пожалуйста, войдите заново.<br>
        <span style="font-size: 0.95em; color: #888;">Вы будете перенаправлены на страницу входа...</span>
      </div>
    `;
    document.body.appendChild(modal);
  }

  // =====================
  // === СОРТИРОВКА ======
  // =====================
  function setupSortHandlers() {
    const sortLinks = document.querySelectorAll(config.sortLinksSelector);
    sortLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        const col = this.dataset.sort;
        if (sortBy === col) {
          sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          sortBy = col;
          sortDir = 'asc';
        }
        currentPage = 1;
        fetchPage();
      });
    });
  }

  function updateSortIcons() {
    document.querySelectorAll(config.sortLinksSelector).forEach(link => {
      const icon = link.querySelector('.sort-icon');
      const col = link.dataset.sort;
      if (!icon) return;
      if (col === sortBy && sortBy !== config.defaultSortBy && sortBy !== '') {
        icon.innerHTML = sortDir === 'asc' ? svgAsc : svgDesc;
      } else {
        icon.innerHTML = svgDefault;
      }
    });
    // Мобильная иконка и select
    const mobSortName = document.getElementById(config.mobSortNameId);
    const mobSorting = document.getElementById(config.mobSortingId);
    if (mobSortName) {
      mobSortName.dataset.dir = sortDir;
      const icon = mobSortName.querySelector('.sort-icon');
      if (icon) {
        // Если сортировка не выбрана или дефолтная - показываем дефолтную иконку
        if (sortBy === '' || sortBy === config.defaultSortBy) {
          icon.innerHTML = svgDefault;
        } else {
          // Иначе показываем активную иконку с правильным направлением
          icon.innerHTML = sortDir === 'desc' ? svgDesc : svgAsc;
        }
      }
    }
    if (mobSorting) {
      mobSorting.value = sortBy === '' ? '' : sortBy;
    }
  }

  // =====================
  // === ФИЛЬТРЫ =========
  // =====================
  function setupFilterHandlers() {
    config.filterInputs.forEach(sel => {
      const el = document.querySelector(sel);
      if (!el) return;
      if (el.tagName === 'INPUT') {
        el.addEventListener('keydown', function(e) {
          if (e.key === 'Enter') {
            currentPage = 1;
            fetchPage();
          }
        });
      } else {
        el.addEventListener('change', function() {
          currentPage = 1;
          fetchPage();
        });
      }
    });
  }

  // =====================
  // === ПАГИНАЦИЯ =======
  // =====================
  function setupPaginationHandlers() {
    const pag = document.querySelector(config.paginationSelector);
    if (!pag) return;
    pag.addEventListener('click', function(e) {
      const btn = e.target.closest('[data-page]');
      if (!btn) return;
      const page = parseInt(btn.dataset.page, 10);
      if (!isNaN(page)) {
        currentPage = page;
        fetchPage();
      }
    });
  }

  function setupPageLimitDropdown() {
    const pageLimitBtn = document.getElementById('page-limit-button');
    const pageLimitDropdown = document.getElementById('page-limit-dropdown');
    const pageLimitText = document.getElementById('page-limit-text');
    
    if (!pageLimitBtn || !pageLimitDropdown || !pageLimitText) return;

    // Открытие/закрытие dropdown
    pageLimitBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      pageLimitDropdown.classList.toggle('hidden');
    });

    // Закрытие при клике вне
    document.addEventListener('click', function(e) {
      if (!e.target.closest('#page-limit-button')) {
        pageLimitDropdown.classList.add('hidden');
      }
    });

    // Обработка выбора лимита
    pageLimitDropdown.querySelectorAll('[data-value]').forEach(item => {
      item.addEventListener('click', function() {
        const newLimit = parseInt(this.getAttribute('data-value'), 10);
        pageLimitText.textContent = `${newLimit} on page`;
        pageLimitDropdown.classList.add('hidden');
        setPageLimit(newLimit);
      });

      // Hover эффекты
      item.addEventListener('mouseenter', function() {
        this.classList.add('bg-[#E6E9F5]'); 
      });
      item.addEventListener('mouseleave', function() {
        this.classList.remove('bg-[#E6E9F5]');
      });
    });
  }

  function renderPagination(limit, page, total, totalPages) {
    const pag = document.querySelector(config.paginationSelector); // '#pagination-controls'
    const pagInfo = document.getElementById('pagination-info');
    if (!pag) return;

    // Инфо-блок
    if (pagInfo) {
      const from = total === 0 ? 0 : (page - 1) * limit + 1;
      const to = Math.min(page * limit, total);
      pagInfo.textContent = `Goods ${from}-${to} from ${total}`;
    }

    // Если страниц 1 — не показываем кнопки
    if (totalPages <= 1) {
      pag.innerHTML = '';
      return;
    }

    pag.innerHTML = '';

    // Кнопка «назад»
    if (page > 1) {
      pag.innerHTML += `<button class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-200 text-gray-500 hover:bg-[#A3B8F8] hover:text-white transition" data-page="${page - 1}">&lt;</button>`;
    }

    // Диапазон страниц с многоточиями
    let start = Math.max(1, page - 2), end = Math.min(totalPages, page + 2);
    if (start > 1) pag.innerHTML += `<button class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-200 text-gray-500 hover:bg-[#A3B8F8] hover:text-white transition" data-page="1">1</button><span>...</span>`;
    for (let i = start; i <= end; i++) {
      pag.innerHTML += `<button class="w-8 h-8 flex items-center justify-center rounded-full ${i === page ? 'bg-[#A3B8F8] text-white font-bold' : 'bg-gray-200 text-gray-500 hover:bg-[#A3B8F8] hover:text-white transition'}" data-page="${i}">${i}</button>`;
    }
    if (end < totalPages) pag.innerHTML += `<span>...</span><button class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-200 text-gray-500 hover:bg-[#A3B8F8] hover:text-white transition" data-page="${totalPages}">${totalPages}</button>`;

    // Кнопка «вперёд»
    if (page < totalPages) {
      pag.innerHTML += `<button class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-200 text-gray-500 hover:bg-[#A3B8F8] hover:text-white transition" data-page="${page + 1}">&gt;</button>`;
    }

    // Навешиваем обработчики
    pag.querySelectorAll('button[data-page]').forEach(btn => {
      btn.addEventListener('click', function() {
        currentPage = parseInt(this.dataset.page, 10);
        fetchPage();
      });
    });
  }

  // =====================
  // === СБРОС СОРТИРОВКИ =
  // =====================
  function setupResetSortHandler() {
    const btn = document.querySelector(config.resetSortBtnSelector);
    if (!btn) return;
    btn.addEventListener('click', function() {
      sortBy = config.defaultSortBy;
      sortDir = config.defaultSortDir;
      currentPage = 1;
      fetchPage();
    });
  }


  // =====================
  // === ФИЛЬТРАЦИЯ =======
  // =====================
  function setupFilterToggleHandler() {
    const filterBtn = document.querySelector(config.filterBtnSelector);
    const filterRow = document.querySelector(config.filterRowSelector);
    const filterIcon = document.querySelector(config.filterIconSelector);
    const filterIconActive = document.querySelector(config.filterIconActiveSelector);
    if (!filterBtn || !filterRow || !filterIcon || !filterIconActive) return;
    filterBtn.addEventListener('click', function(e) {
      e.preventDefault();
      const isHidden = filterRow.classList.contains('hidden');
      if (isHidden) {
        filterRow.classList.remove('hidden');
        filterIcon.classList.add('hidden');
        filterIconActive.classList.remove('hidden');
        filterBtn.classList.add('text-[#88A6F0]');
        filterRow.querySelector('input')?.focus();
      } else {
        filterRow.classList.add('hidden');
        filterIcon.classList.remove('hidden');
        filterIconActive.classList.add('hidden');
        filterBtn.classList.remove('text-[#88A6F0]');
        // Сброс фильтров и обновление таблицы
        config.filterInputs.forEach(sel => {
          const inp = document.querySelector(sel);
          if (!inp) return;
          if (inp.tagName === 'SELECT') inp.selectedIndex = 0;
          else inp.value = '';
        });
        fetchPage();
      }
    });
  }

  // =====================
  // === SVG ICONS =======
  // =====================
  const svgDefault = `<svg width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg"><g clip-path="url(#clip0_886_851)"><path d="M4.26624 8.69067L6.62335 6.33356L8.98047 8.69067" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.62505 6.33354L6.62505 14.5834" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M15.5625 13.0594L13.2054 15.4166L10.8483 13.0594" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M13.2071 7.16667L13.2071 15.4166" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></g><defs><clipPath id="clip0_886_851"><rect width="20" height="20" fill="white" transform="translate(0 0.5)"/></clipPath></defs></svg>`;
  const svgAsc = `<svg width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg"><rect y="0.5" width="20" height="20" rx="5" fill="white"/><path d="M7.75091 8.69031L10.0805 6.33319L12.4102 8.69031" stroke="#88A6F0" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M10.0794 6.3333L10.0794 14.5832" stroke="#88A6F0" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const svgDesc = `<svg width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg"><rect y="0.5" width="20" height="20" rx="5" fill="white"/><path d="M12.4805 13.0596L10.1234 15.4167L7.76624 13.0596" stroke="#88A6F0" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M10.125 7.1668L10.125 15.4167" stroke="#88A6F0" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

  // =====================
  // === API =============
  // =====================
  function updateSortBtnIcon(sortByVal, sortDirVal) {
    const sortBtn = document.querySelector(config.sortBtnSelector);
    const sortIcon = document.querySelector(config.sortIconSelector);
    const sortIconActive = document.querySelector(config.sortIconActiveSelector);
    if (!sortBtn || !sortIcon || !sortIconActive) return;
    if ((sortByVal || sortBy) === config.defaultSortBy && (sortDirVal || sortDir) === config.defaultSortDir) {
      sortIcon.classList.remove('hidden');
      sortIconActive.classList.add('hidden');
      sortBtn.classList.remove('text-[#88A6F0]');
      sortBtn.classList.add('text-black');
    } else {
      sortIcon.classList.add('hidden');
      sortIconActive.classList.remove('hidden');
      sortBtn.classList.remove('text-black');
      sortBtn.classList.add('text-[#88A6F0]');
    }
  }

  function setPageLimit(newLimit) {
    pageLimit = newLimit;
    currentPage = 1;
    
    // Синхронизируем мобильный селектор
    const mobileLimit = document.getElementById('mobile_limit');
    if (mobileLimit) {
      mobileLimit.value = newLimit;
    }
    
    // Синхронизируем десктопный селектор
    const pageLimitText = document.getElementById('page-limit-text');
    if (pageLimitText) {
      pageLimitText.textContent = `${newLimit} on page`;
    }
    
    fetchPage();
  }

  function setFilters(filters) {
    if (!filters || typeof filters !== 'object') return;
    // 1. Обновить sortBy/sortDir
    if (filters.sort_by === '') {
      sortBy = '';
      sortDir = config.defaultSortDir;
    } else if (filters.sort_by === undefined) {
      sortBy = config.defaultSortBy;
      sortDir = config.defaultSortDir;
    } else {
      if (filters.sort_by !== undefined) sortBy = filters.sort_by;
      if (filters.sort_dir !== undefined) sortDir = filters.sort_dir;
    }
    // 2. Обновить значения всех инпутов (и моб, и десктоп)
    config.filterInputs.forEach(sel => {
      const el = document.querySelector(sel);
      if (!el) return;
      const key = el.name || el.id;
      if (filters.hasOwnProperty(key)) {
        el.value = filters[key];
      }
    });
    // 3. Обновить визуал сортировки
    updateSortIcons();
    // 4. Обновить URL и данные
    if (filters.page) {
      currentPage = parseInt(filters.page, 10) || 1;
    } else {
      currentPage = 1;
    }
    if (filters.limit) {
      pageLimit = parseInt(filters.limit, 10) || config.defaultFilters?.limit || 10;
    }
    fetchPage();
  }

  // =====================
  // === МОБИЛЬНАЯ ПАГИНАЦИЯ ===
  // =====================
  function renderMobilePagination({limit, page, total, total_pages}) {
    if (!config.mobilePaginationInfoSelector || !config.mobilePaginationControlsSelector) return;
    const info = document.querySelector(config.mobilePaginationInfoSelector);
    const controls = document.querySelector(config.mobilePaginationControlsSelector);
    if (!info || !controls) return;
    const from = total === 0 ? 0 : (page - 1) * limit + 1;
    const to = Math.min(page * limit, total);
    info.textContent = `Показано ${from}-${to} из ${total}`;
    controls.innerHTML = '';
    if (page > 1) {
      controls.innerHTML += `<button data-page="${page-1}" class="px-2 py-1 rounded bg-gray-200">←</button>`;
      controls.innerHTML += `<button data-page="${page-1}" class="px-2 py-1 rounded bg-gray-200">${page-1}</button>`;
    }
    controls.innerHTML += `<button class="px-2 py-1 rounded bg-[#A3B8F8] text-white font-bold">${page}</button>`;
    if (page < total_pages) {
      controls.innerHTML += `<button data-page="${page+1}" class="px-2 py-1 rounded bg-gray-200">${page+1}</button>`;
      controls.innerHTML += `<button data-page="${page+1}" class="px-2 py-1 rounded bg-gray-200">→</button>`;
    }
    controls.querySelectorAll('button[data-page]').forEach(btn => {
      btn.onclick = () => {
        setFilters({ ...getAllFiltersAndSort(), page: parseInt(btn.dataset.page, 10) });
      };
    });
  }

  function setupMobilePaginationObserver() {
    if (!config.mobileCardsContainerSelector || !config.mobilePaginationContainerSelector) return;
    const cards = document.querySelectorAll(config.mobileCardsContainerSelector + ' .card');
    const mobilePag = document.querySelector(config.mobilePaginationContainerSelector);
    if (!mobilePag) return;
    if (!cards.length) {
      mobilePag.classList.add('hidden');
      if (mobilePaginationObserver) mobilePaginationObserver.disconnect();
      return;
    }
    const lastCard = cards[cards.length - 1];
    if (!lastCard) {
      mobilePag.classList.add('hidden');
      if (mobilePaginationObserver) mobilePaginationObserver.disconnect();
      return;
    }
    if (mobilePaginationObserver) {
      mobilePaginationObserver.disconnect();
    }
    mobilePaginationObserver = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        mobilePag.classList.remove('hidden');
      } else {
        mobilePag.classList.add('hidden');
      }
    }, { threshold: 0.05 });
    mobilePaginationObserver.observe(lastCard);
    // Показывать всегда, если карточек меньше лимита
    const limit = parseInt(document.getElementById('mobile_limit')?.value || '10', 10);
    if (cards.length < limit) {
      mobilePag.classList.remove('hidden');
      return;
    }
    requestAnimationFrame(() => {
      const rect = lastCard.getBoundingClientRect();
      const inView = rect.top < window.innerHeight && rect.bottom > 0;
      if (inView) {
        mobilePag.classList.remove('hidden');
      } else {
        mobilePag.classList.add('hidden');
      }
    });
  }

  // В afterUpdateTable добавить вызовы мобильной пагинации
  function afterUpdateTableMobilePagination(data) {
    if (config.mobilePaginationInfoSelector && config.mobilePaginationControlsSelector) {
      renderMobilePagination({
        limit: data.limit,
        page: data.page,
        total: data.total,
        total_pages: data.total_pages
      });
      setupMobilePaginationObserver();
    }
  }

  // =====================
  // === МОБИЛЬНЫЕ ФУНКЦИИ ===
  // =====================
  function clearMobileFilters() {
    if (!config.mobileFilterInputs) return;
    config.mobileFilterInputs.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    
    // Сбрасываем мобильный лимит страниц на дефолтное значение
    const mobileLimit = document.getElementById('mobile_limit');
    if (mobileLimit) {
      mobileLimit.value = '10';
    }
  }

  function updateMobFilterRowState() {
    const mobFilterIcon = document.getElementById(config.mobFilterIconId || 'mob-filter-icon');
    const mobFilterIconActive = document.getElementById(config.mobFilterIconActiveId || 'mob-filter-icon-active');
    const mobFilterRowBtn = document.getElementById(config.mobFilterRowBtnId || 'mob-filter-row');
    
    if (!mobFilterIcon || !mobFilterIconActive || !mobFilterRowBtn) {
      return;
    }

    const params = new URLSearchParams(window.location.search);
    let hasFilter = false;
    
    if (config.mobileFilterInputs) {
      config.mobileFilterInputs.forEach(id => {
        const el = document.getElementById(id);
        const key = el?.name || id.replace(/^mob_search_|^mob_/, '');
        if (params.get(key)) hasFilter = true;
      });
    }
    
    if (hasFilter) {
      mobFilterIcon.classList.add('hidden');
      mobFilterIconActive.classList.remove('hidden');
      mobFilterRowBtn.classList.add('text-[#88A6F0]');
    } else {
      mobFilterIcon.classList.remove('hidden');
      mobFilterIconActive.classList.add('hidden');
      mobFilterRowBtn.classList.remove('text-[#88A6F0]');
    }
  }

  function syncMobileFiltersWithUrl() {
    if (!config.mobileFilterInputs) return;
    const params = new URLSearchParams(window.location.search);
    config.mobileFilterInputs.forEach(id => {
      const el = document.getElementById(id);
      if (!el) {
        return;
      }
      const key = el.name || id.replace(/^mob_search_|^mob_/, '');
      if (params.has(key)) {
        el.value = params.get(key);
      } else {
        el.value = '';
      }
    });
    
    // Синхронизируем мобильный лимит страниц
    const mobileLimit = document.getElementById('mobile_limit');
    if (mobileLimit && params.has('limit')) {
      mobileLimit.value = params.get('limit');
    }
  }

  function updateMobSortIcon(dir) {
    const mobSortName = document.getElementById(config.mobSortNameId || 'mob_sort_name');
    const icon = mobSortName?.querySelector('.sort-icon');
    if (!icon) return;
    
    // Используем глобальные SVG иконки
    icon.innerHTML = dir === 'desc' ? svgDesc : svgAsc;
  }

  function syncMobileSortWithUrl() {
    const mobSorting = document.getElementById(config.mobSortingId || 'mob_sorting');
    const mobSortName = document.getElementById(config.mobSortNameId || 'mob_sort_name');
    
    if (!mobSorting || !mobSortName) {
      return;
    }
    
    const params = new URLSearchParams(window.location.search);
    let sortBy = params.get('sort_by') || '';
    let sortDir = params.get('sort_dir') || 'asc';
    
    mobSorting.value = sortBy;
    mobSortName.dataset.dir = sortDir;
    
    // Обновляем иконку в зависимости от состояния сортировки
    const icon = mobSortName.querySelector('.sort-icon');
    if (icon) {
      if (sortBy === '' || sortBy === config.defaultSortBy) {
        icon.innerHTML = svgDefault;
      } else {
        icon.innerHTML = sortDir === 'desc' ? svgDesc : svgAsc;
      }
    }
  }

  function setupMobileHandlers() {
    // Мобильная кнопка очистки фильтров
    const mobFilterRowBtn = document.getElementById(config.mobFilterRowBtnId || 'mob-filter-row');
    if (mobFilterRowBtn) {
      mobFilterRowBtn.addEventListener('click', function(e) {
        e.preventDefault();
        clearMobileFilters();
        updateMobFilterRowState();
        // Очистка всех фильтров
        const clearFilters = {};
        if (config.filterKeys) {
          config.filterKeys.forEach(key => {
            clearFilters[key] = '';
          });
        }
        setFilters(clearFilters);
      });
    }

    // Мобильная сортировка
    const mobSorting = document.getElementById(config.mobSortingId || 'mob_sorting');
    const mobSortName = document.getElementById(config.mobSortNameId || 'mob_sort_name');
    
    if (mobSorting) {
      mobSorting.addEventListener('change', function() {
        const selectedSortBy = mobSorting.value;
        
        if (selectedSortBy === '') {
          // Если сортировка отключена - показываем дефолтную иконку
          mobSortName.dataset.dir = 'asc';
          const icon = mobSortName?.querySelector('.sort-icon');
          if (icon) icon.innerHTML = svgDefault;
        } else {
          // Если выбрана новая сортировка - устанавливаем asc и показываем активную иконку
          mobSortName.dataset.dir = 'asc';
          updateMobSortIcon('asc');
        }
        
        const filters = getAllFiltersAndSort();
        filters.sort_by = selectedSortBy;
        filters.sort_dir = mobSortName?.dataset.dir || 'asc';
        setFilters(filters);
      });
    }
    
    if (mobSortName) {
      mobSortName.addEventListener('click', function(e) {
        e.preventDefault();
        if (!mobSorting?.value) return;
        
        // Логика как в десктопной версии
        const currentSortBy = mobSorting.value;
        const currentSortDir = mobSortName.dataset.dir || 'asc';
        
        if (sortBy === currentSortBy) {
          // Если та же колонка - меняем направление
          const newDir = currentSortDir === 'asc' ? 'desc' : 'asc';
          mobSortName.dataset.dir = newDir;
          updateMobSortIcon(newDir);
        } else {
          // Если новая колонка - устанавливаем asc
          mobSortName.dataset.dir = 'asc';
          updateMobSortIcon('asc');
        }
        
        // Применяем сортировку
        const filters = getAllFiltersAndSort();
        filters.sort_by = mobSorting.value;
        filters.sort_dir = mobSortName.dataset.dir;
        setFilters(filters);
      });
    }

    // Мобильный фильтр "Применить"
    const mobileFilterApply = document.getElementById(config.mobileFilterApplyId || 'mobileFilterApply');
    if (mobileFilterApply) {
      mobileFilterApply.addEventListener('click', function() {
        const filters = {};
        
        // Собираем значения мобильных фильтров
        if (config.mobileFilterInputs) {
          config.mobileFilterInputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
              const key = el.name || id.replace(/^mob_search_|^mob_/, '');
              filters[key] = el.value || '';
            }
          });
        }
        
        // Добавляем сортировку
        const sortBy = mobSorting?.value || '';
        const sortDir = mobSortName?.dataset.dir || 'asc';
        if (sortBy) {
          filters.sort_by = sortBy;
          filters.sort_dir = sortDir;
        } else {
          filters.sort_by = '';
          filters.sort_dir = 'asc';
        }
        
        setFilters(filters);
        
        // Закрываем мобильный фильтр
        if (typeof closeMobileFilter === 'function') {
          closeMobileFilter();
        } else if (window.closeModal) {
          window.closeModal('mobile-filter');
        }
      });
    }

    // Кнопка открытия мобильного фильтра
    const mobileFilterBtn = document.getElementById(config.mobileFilterBtnId || 'mobile-filter');
    if (mobileFilterBtn) {
      mobileFilterBtn.addEventListener('click', function() {
        if (window.openModal) window.openModal('mobile-filter');
        // Синхронизируем после небольшой задержки, чтобы модальное окно успело открыться
        setTimeout(() => {
          syncMobileFiltersWithUrl();
          syncMobileSortWithUrl();
          updateMobFilterRowState();
        }, 100);
      });
    }

    // Мобильный лимит страниц
    const mobileLimit = document.getElementById('mobile_limit');
    if (mobileLimit) {
      mobileLimit.addEventListener('change', function() {
        const newLimit = parseInt(this.value, 10);
        setPageLimit(newLimit);
      });
    }

    // Слушатель для синхронизации при открытии мобильного фильтра
    window.addEventListener('modalOpened', function(event) {
      if (event.detail.type === 'mobile-filter') {
        // Мобильный фильтр открылся, синхронизируем данные
        setTimeout(() => {
          syncMobileFiltersWithUrl();
          syncMobileSortWithUrl();
          updateMobFilterRowState();
        }, 100);
      }
    });
  }

  function setupCardActivation() {
    if (config.cardActivationInitialized) return;
    config.cardActivationInitialized = true;

    const cardsContainer = document.querySelector(config.cardsContainerSelector);
    if (!cardsContainer) return;

    cardsContainer.addEventListener('click', function(e) {
      const card = e.target.closest('.card');
      if (!card) return;
      
      cardsContainer.querySelectorAll('.card.active').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      e.stopPropagation();
    });
  }

  function setupCardDeactivation() {
    if (config.cardDeactivationInitialized) return;
    config.cardDeactivationInitialized = true;

    document.body.addEventListener('click', function(e) {
      if (!e.target.closest('.card')) {
        document.querySelectorAll('.card.active').forEach(card => {
          card.classList.remove('active');
        });
      }
    });
  }

  function showToast(message, opts = {}) {
    let toast = document.createElement('div');
    toast.className = 'custom-toast';
    toast.textContent = message;
    Object.assign(toast.style, {
      position: 'fixed',
      left: '50%',
      bottom: '32px',
      transform: 'translateX(-50%)',
      background: '#323A4B',
      color: 'white',
      padding: '14px 32px',
      borderRadius: '12px',
      fontSize: '1rem',
      boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
      zIndex: 9999,
      opacity: 0,
      transition: 'opacity 0.3s',
      pointerEvents: 'none',
      ...opts.style
    });
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = 1; }, 10);
    setTimeout(() => {
      toast.style.opacity = 0;
      setTimeout(() => toast.remove(), 300);
    }, opts.duration || 3500);
  }

  return {
    init,
    destroy: cleanup, // Добавляем функцию очистки
    fetchPage, // экспортируем для ручного вызова
    updateSortIcons,
    updateTable,
    getAllFiltersAndSort,
    getNonDefaultFiltersForUrl, // новая функция для URL без дефолтных значений
    getFilterValues,
    renderPagination,
    updateSortBtnIcon, // экспортируем для ручного вызова
    setPageLimit, // для кастомного dropdown
    setFilters, // новый API для явного применения фильтров
    clearMobileFilters,
    updateMobFilterRowState,
    syncMobileFiltersWithUrl,
    syncMobileSortWithUrl,
    setupCardActivation,
    setupCardDeactivation,
    showToast,
    config: config
  };
})();

// Для использования: TableUtils.init({...})
window.TableUtils = TableUtils;