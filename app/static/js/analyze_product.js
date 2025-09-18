// =====================
// === CONSTANTS =======
// =====================
const ANALYZE_PRODUCT_CONFIG = {
  SELECTORS: {
    NEW_PRODUCT_BTN: 'new_product',
    ADD_REVIEW_BTN: 'add-review-btn',
    CLEAR_REVIEWS_BTN: 'clear-reviews-btn',
    REVIEWS_TBODY: 'reviews-tbody',
    PRODUCT_CARDS: 'product-cards',
    REVIEW_MODAL: 'review-modal',
    REVIEW_FORM: 'review-form',
    CLOSE_MODAL_BTN: 'close-modal-btn',
    ANALYZE_BUTTON: 'analyze-button',
    UPLOADING_FILES_BTN: 'uploading-files-btn',
    UPLOADING_FILES: 'uploading-files'
  },
  ROUTES: {
    NEW_PRODUCT: '/product/new/form',
    ANALYZE_PRODUCT: '/analyze/{id}/form',
    EDIT_PRODUCT: '/product/{id}/form'
  },
  MESSAGES: {
    NO_REVIEWS: 'Нет отзывов',
    DELETE_ERROR: 'Ошибка при удалении отзыва',
    SAVE_ERROR: 'Ошибка при сохранении отзыва'
  }
};

// =========================
// === ANALYZE PRODUCT MANAGER ===
// =========================
class AnalyzeProductManager {
  constructor() {
    this.newProductBtn = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.NEW_PRODUCT_BTN);
    this.addReviewBtn = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.ADD_REVIEW_BTN);
    this.clearReviewsBtn = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.CLEAR_REVIEWS_BTN);
    this.reviewsTBody = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.REVIEWS_TBODY);
    this.reviewModal = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.REVIEW_MODAL);
    this.reviewForm = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.REVIEW_FORM);
    this.closeModalBtn = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.CLOSE_MODAL_BTN);
    this.analyzeButton = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.ANALYZE_BUTTON);
    this.uploadingFilesBtn = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.UPLOADING_FILES_BTN);
    this.uploadingFiles = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.UPLOADING_FILES);
    
    this.productId = this.analyzeButton?.dataset.productId;
    this.productCardsContainer = document.getElementById(ANALYZE_PRODUCT_CONFIG.SELECTORS.PRODUCT_CARDS);
    
    // Состояние блока загрузки файлов
    this.isUploadingFilesVisible = false;
    
    this.init();
  }

  // Метод для определения текущих фильтров и их статуса
  getCurrentFiltersStatus() {
    try {
      // Получаем текущие фильтры и сортировку
      const currentFilters = TableUtils.getAllFiltersAndSort();
      
      // Определяем дефолтные фильтры (пустые значения)
      const defaultFilters = {
        page: 1,
        limit: 10,
        sort_by: 'id',
        sort_dir: 'desc'
      };
      
      // Проверяем, какие фильтры отличаются от дефолтных
      const nonDefaultFilters = {};
      let hasNonDefaultFilters = false;
      
      for (const [key, value] of Object.entries(currentFilters)) {
        // Пропускаем служебные поля
        if (['page', 'limit', 'sort_by', 'sort_dir'].includes(key)) {
          continue;
        }
        
        // Проверяем, есть ли значение фильтра (не пустое)
        if (value && value !== '' && value !== null && value !== undefined) {
          nonDefaultFilters[key] = value;
          hasNonDefaultFilters = true;
        }
      }
      
      const result = {
        currentFilters: currentFilters,
        defaultFilters: defaultFilters,
        nonDefaultFilters: nonDefaultFilters,
        hasNonDefaultFilters: hasNonDefaultFilters,
        isDefaultState: !hasNonDefaultFilters
      };
      
      return result;
      
    } catch (error) {
      return {
        currentFilters: {},
        defaultFilters: {},
        nonDefaultFilters: {},
        hasNonDefaultFilters: false,
        isDefaultState: true,
        error: error.message
      };
    }
  }

  init() {
    this.bindEvents();
    this.initTableUtils();
    this.initUploadingFiles();
    this.initAnalysisResult();
  }

  bindEvents() {
    // Кнопка создания товара
    this.newProductBtn?.addEventListener('click', (event) => this.handleNewProduct(event));
    
    // Кнопка добавления отзыва
    this.addReviewBtn?.addEventListener('click', (event) => this.handleAddReview(event));
    
    // Кнопка очистки отзывов
    this.clearReviewsBtn?.addEventListener('click', (event) => this.handleClearReviews(event));
    
    // Кнопка показа блока загрузки файлов
    const showUploadBtn = document.getElementById('show-upload-btn');
    showUploadBtn?.addEventListener('click', (event) => this.showUploadSection(event));
    
    // Кнопка скрытия блока загрузки файлов
    const hideUploadBtn = document.getElementById('hide-upload-btn');
    hideUploadBtn?.addEventListener('click', (event) => this.hideUploadSection(event));
    
    // Обработка удаления отзывов и редактирования в таблице
    this.reviewsTBody?.addEventListener('click', (event) => {
      this.handleDeleteReview(event);
      this.handleEditReview(event);
    });
    
    // Обработка редактирования и удаления в карточках (мобильные устройства)
    // Используем делегирование событий для динамически созданных элементов
    document.addEventListener('click', (event) => {
      // Проверяем, является ли кликнутый элемент кнопкой редактирования
      const editBtn = event.target.closest('.edit-review-btn');
      if (editBtn) {
        event.preventDefault();
        event.stopPropagation();
        this.handleEditReview(event);
        return;
      }
      
      // Проверяем, является ли кликнутый элемент кнопкой удаления
      // Но только если это НЕ в таблице (избегаем дублирования)
      const deleteBtn = event.target.closest('.delete-btn');
      if (deleteBtn && !this.reviewsTBody?.contains(deleteBtn)) {
        event.preventDefault();
        event.stopPropagation();
        this.handleDeleteReview(event);
        return;
      }
    });
    
    // Дополнительный обработчик для контейнера карточек
    this.productCardsContainer?.addEventListener('click', (event) => {
      const deleteBtn = event.target.closest('.delete-btn');
      if (deleteBtn) {
        event.preventDefault();
        event.stopPropagation();
        this.handleDeleteReview(event);
        return;
      }
    });
    
    // Модальное окно отзыва
    this.closeModalBtn?.addEventListener('click', (event) => this.closeReviewModal(event));
    this.reviewForm?.addEventListener('submit', (event) => this.handleSaveReview(event));
    
    // Закрытие модального окна при клике вне
    this.reviewModal?.addEventListener('click', (event) => {
      if (event.target === this.reviewModal) {
        this.closeReviewModal(event);
      }
    });
    
    // Кнопка анализа
    this.analyzeButton?.addEventListener('click', (event) => this.handleAnalyze(event));
    
    // Кнопка переключения блока загрузки файлов
    this.uploadingFilesBtn?.addEventListener('click', (event) => this.toggleUploadingFiles(event));
  }

  initTableUtils() {
    const tableUtilsConfig = {
      tableSelector: '#reviews-table',
      tbodySelector: '#reviews-tbody',
      filterRowSelector: '#tab_search',
      filterInputs: [
        '#tab_search_importance',
        '#tab_search_source', 
        '#tab_search_text',
        '#tab_search_advantages',
        '#tab_search_disadvantages',
        '#tab_search_normalized_rating'
      ],
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
      dataUrl: '/analyze/data',
      renderRow: this.renderReviewRow.bind(this),
      renderCards: this.renderReviewCards.bind(this),
      cardsContainerSelector: '#product-cards',
      defaultFilters: {
        product_id: this.productId,
        limit: 10
      },
      afterUpdateTable: this.afterUpdateTable.bind(this),
      mobilePaginationInfoSelector: '#mobile-pagination-info',
      mobilePaginationControlsSelector: '#mobile-pagination-controls',
      mobilePaginationContainerSelector: '#mobile-pagination',
      mobileCardsContainerSelector: '#product-cards',
      mobileFilterInputs: [
        'mob_search_importance',
        'mob_search_source',
        'mob_search_text', 
        'mob_search_advantages',
        'mob_search_disadvantages',
        'mob_search_normalized_rating'
      ],
      mobSortingId: 'mob_sorting',
      mobSortNameId: 'mob_sort_name',
      mobFilterRowBtnId: 'mob-filter-row',
      mobFilterIconId: 'mob-filter-icon',
      mobFilterIconActiveId: 'mob-filter-icon-active',
      mobileFilterApplyId: 'mobileFilterApply',
      mobileFilterBtnId: 'mobile-filter',
      mobileLimitSelector: '#mobile_limit',
      filterKeys: ['importance', 'source', 'text', 'advantages', 'disadvantages', 'normalized_rating']
    };
    
    // Инициализация универсального механизма для таблицы отзывов
    TableUtils.init(tableUtilsConfig);
  }

  renderReviewRow(review) {
    return `
      <tr 
        id="review-row-${review.id}"
        data-raw_rating="${review.raw_rating || ''}"
        data-rating="${review.rating || 0}"
        data-max_rating="${review.max_rating || 0}"
        data-normalized_rating="${review.normalized_rating || 0}"
        class="h-[80px] align-middle border-b border-gray-200 table-row cursor-pointer"
      >
        <td class="w-[60px] p-[5px] align-middle text-gray-700" data-field="importance">${review.importance || ''}</td>
        <td class="w-[125px] p-[5px] align-middle text-gray-700" data-field="source">${review.source || ''}</td>
        <td class="p-[5px] align-middle font-semibold text-gray-900 line-clamp-3" data-field="text">${review.text || ''}</td>
        <td class="w-[200px] p-[5px] align-middle text-gray-700" data-field="advantages">${review.advantages || ''}</td>
        <td class="w-[200px] p-[5px] align-middle text-gray-700" data-field="disadvantages">${review.disadvantages || ''}</td>
        <td class="w-[100px] p-[5px] align-middle text-gray-700">
          <div class="flex flex-col items-start">
            <span>${review.raw_rating || (review.rating || 0) + '/' + (review.max_rating || 0)}</span>
            <span class="flex items-center text-xs text-blue-600 font-semibold mt-0.5">
              <svg class="w-4 h-4 mr-1 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.122-6.545L.488 6.91l6.561-.955L10 0l2.951 5.955 6.561.955-4.756 4.635 1.122 6.545z"/></svg>
              ${review.normalized_rating || 0}%
            </span>
          </div>
        </td>
        <td class="w-[100px] p-[5px]">
          <div class="flex items-center gap-2">
            <a href="#" class="rounded-full hover:bg-gray-200 transition p-1" title="Edit" data-id="${review.id}" data-product-id="${review.product_id}">
              <svg width="24" height="24" viewBox="0 0 35 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="0.5" y="1" width="34" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                <path d="M18.9769 13.0492C18.9769 13.0492 19.0487 14.2805 20.135 15.3661C21.2212 16.4523 22.4519 16.5248 22.4519 16.5248L23.0312 15.9455C23.4921 15.4846 23.7511 14.8594 23.7511 14.2076C23.7511 13.5558 23.4921 12.9307 23.0312 12.4698C22.5704 12.0089 21.9452 11.75 21.2934 11.75C20.6416 11.75 20.0165 12.0089 19.5556 12.4698L18.9762 13.0492L17.5012 14.5242M22.4519 16.5242L19.1644 19.813L17.2262 21.7498L17.1262 21.8505C16.765 22.2111 16.5844 22.3917 16.3856 22.5467C16.151 22.7296 15.8972 22.8865 15.6287 23.0148C15.4012 23.123 15.1594 23.2036 14.675 23.3648L12.6244 24.0486M12.6244 24.0486L12.1231 24.2161C12.0063 24.2553 11.8808 24.2611 11.7609 24.2329C11.6409 24.2047 11.5312 24.1435 11.444 24.0564C11.3569 23.9693 11.2958 23.8595 11.2676 23.7396C11.2394 23.6196 11.2452 23.4942 11.2844 23.3773L11.4519 22.8761M12.6244 24.0486L11.4519 22.8761M11.4519 22.8761L12.1356 20.8255C12.2969 20.3411 12.3775 20.0992 12.4856 19.8717C12.6144 19.6021 12.7704 19.3498 12.9537 19.1148C13.1087 18.9161 13.2894 18.7355 13.65 18.3748L15.3137 16.7117" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
            </a>
            <button class="rounded-full hover:bg-red-100 transition p-1 delete-btn" title="Delete" data-id="${review.id}">
              <svg width="24" height="24" viewBox="0 0 33 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="0.5" y="1" width="32" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                <path d="M11 12.5L11.7639 24.3182C11.8002 25.0011 12.3139 25.5 12.9861 25.5H20.0139M21.4844 21.142L22 12.5" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 12.5H23H10Z" fill="#6B6397"/>
                <path d="M10 12.5H23" stroke="#6B6397" stroke-width="1.2" stroke-miterlimit="10" stroke-linecap="round"/>
                <path d="M14.2778 12.8636V11.3864C14.2775 11.2699 14.2988 11.1545 14.3406 11.0468C14.3823 10.9391 14.4437 10.8412 14.5211 10.7589C14.5986 10.6765 14.6906 10.6112 14.7918 10.5668C14.8931 10.5224 15.0016 10.4997 15.1111 10.5H17.8889C17.9984 10.4997 18.1069 10.5224 18.2082 10.5668C18.3094 10.6112 18.4014 10.6765 18.4789 10.7589C18.5563 10.8412 18.6177 10.9391 18.6594 11.0468C18.7012 11.1545 18.7225 11.2699 18.7222 11.3864V12.8636M16.5 15.2273V23.5M14 15.2273L14.2778 23.5M19 15.2273L18.7222 23.5" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>
    `;
  }

  renderReviewCards(reviews, container) {
    if (!container || !reviews || !reviews.length) {
      container.innerHTML = '<div class="text-center text-gray-400 py-8">Нет отзывов</div>';
      return;
    }

    const cardsHTML = reviews.map(review => `
      <div class="card relative bg-white rounded-xl shadow-custom p-[10px] shadow-[0px_2px_6px_0px_rgba(0,0,0,0.25)]" data-id="${review.id}">
        <div class="font-semibold text-sm leading-none tracking-normal align-middle mb-[4px] md:hidden">Отзыв #${review.id}</div>
        <div class="bg-white rounded-xl shadow-custom flex flex-col gap-4">
          <div class="card-wrap">
            <div class="font-semibold text-sm leading-none tracking-normal align-middle mb-[4px] hidden md:block">Отзыв #${review.id}</div>
            <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Importance:</span> ${review.importance || 'N/A'}</div>
            <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Source:</span> ${review.source || 'N/A'}</div>
            <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Text:</span> ${(review.text || '').substring(0, 100)}${(review.text || '').length > 100 ? '...' : ''}</div>
            <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Pros:</span> ${(review.advantages || '').substring(0, 50)}${(review.advantages || '').length > 50 ? '...' : ''}</div>
            <div class="text-sm text-gray-700 mb-[4px]"><span class="font-bold mr-[4px]">Cons:</span> ${(review.disadvantages || '').substring(0, 50)}${(review.disadvantages || '').length > 50 ? '...' : ''}</div>
            <div class="text-sm text-gray-700 mb-[4px]">
              <span class="font-bold mr-[4px]">Rating:</span> 
              <span class="flex items-center text-xs text-blue-600 font-semibold">
                <svg class="w-4 h-4 mr-1 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.122-6.545L.488 6.91l6.561-.955L10 0l2.951 5.955 6.561.955-4.756 4.635 1.122 6.545z"/></svg>
                ${review.normalized_rating || 0}%
              </span>
            </div>
          </div>
          <div class="card-arrow flex justify-end">
            <svg width="14" height="8" viewBox="0 0 14 8" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12.8346 1.25L7.0013 6.75L6.16797 5.96429M1.16797 1.25L3.11214 3.08333" stroke="#1F2125" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <div class="actions flex items-center justify-between gap-2 mt-4 md:mt-0 md:absolute md:right-4 md:bottom-4 relative z-40">
          <button class="edit-review-btn bg-[#A3B8F8] hover:bg-[#7B7FD1] text-white font-semibold px-[20px] py-[5px] rounded-full shadow transition text-[15px] relative z-10" data-id="${review.id}" data-product-id="${review.product_id}">
            Edit
          </button>
          <div class="flex items-center gap-2">
            <button class="rounded-full hover:bg-red-100 transition p-1 delete-btn relative z-50 cursor-pointer" title="Delete" data-id="${review.id}">
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
    `).join('');
    
    container.innerHTML = cardsHTML;
  }

  afterUpdateTable(data) {
    // Дополнительная логика после обновления таблицы
  }

  handleNewProduct(event) {
    event.preventDefault();
    const params = new URLSearchParams(TableUtils.getAllFiltersAndSort());
    window.location.href = `${ANALYZE_PRODUCT_CONFIG.ROUTES.NEW_PRODUCT}?${params.toString()}`;
  }

  handleAddReview(event) {
    event.preventDefault();
    this.openReviewModal();
  }

  handleClearReviews(event) {
    event.preventDefault();
    if (!confirm('Очистить все отзывы для этого товара?')) return;
    
    this.clearReviews();
  }

  handleDeleteReview(event) {
    const deleteBtn = event.target.closest('.delete-btn');
    if (!deleteBtn) return;

    const reviewId = deleteBtn.dataset.id;
    if (!reviewId || !confirm('Удалить этот отзыв?')) return;

    this.deleteReview(reviewId);
  }

  handleEditReview(event) {
    // Проверяем клик по ссылке редактирования в таблице
    const editLink = event.target.closest('a[data-id]');
    if (editLink && editLink.dataset.id) {
      event.preventDefault();
      const reviewId = editLink.dataset.id;
      this.openReviewModal(reviewId);
      return;
    }

    // Проверяем клик по кнопке редактирования в карточках
    const editBtn = event.target.closest('.edit-review-btn');
    if (editBtn && editBtn.dataset.id) {
      event.preventDefault();
      const reviewId = editBtn.dataset.id;
      this.openReviewModal(reviewId);
      return;
    }
  }

  handleSaveReview(event) {
    event.preventDefault();
    this.saveReview();
  }

  openReviewModal(reviewId = null) {
    if (this.reviewModal) {
      this.reviewModal.classList.remove('hidden');
      this.reviewModal.classList.add('flex');
      
      const modalTitle = document.getElementById('modal-title');
      
      if (reviewId) {
        modalTitle.textContent = 'Редактировать отзыв';
        this.loadReviewData(reviewId);
      } else {
        modalTitle.textContent = 'Добавить отзыв';
        this.clearReviewForm();
      }
    }
  }

  closeReviewModal(event) {
    if (event) event.preventDefault();
    if (this.reviewModal) {
      this.reviewModal.classList.add('hidden');
      this.reviewModal.classList.remove('flex');
    }
  }

  clearReviewForm() {
    if (this.reviewForm) {
      this.reviewForm.reset();
      this.reviewForm.querySelector('input[name="review_id"]').value = '';
      this.reviewForm.querySelector('input[name="product_id"]').value = this.productId;
    }
  }

  async loadReviewData(reviewId) {
    try {
      const response = await fetch(`/api/review/${reviewId}`);
      if (response.ok) {
        const review = await response.json();
        this.fillReviewForm(review);
      }
    } catch (error) {
      console.error('Error loading review:', error);
    }
  }

  fillReviewForm(review) {
    if (!this.reviewForm) return;
    
    this.reviewForm.querySelector('input[name="review_id"]').value = review.id;
    this.reviewForm.querySelector('input[name="product_id"]').value = review.product_id;
    this.reviewForm.querySelector('input[name="importance"]').value = review.importance || '';
    this.reviewForm.querySelector('textarea[name="source"]').value = review.source || '';
    this.reviewForm.querySelector('textarea[name="text"]').value = review.text || '';
    this.reviewForm.querySelector('textarea[name="advantages"]').value = review.advantages || '';
    this.reviewForm.querySelector('textarea[name="disadvantages"]').value = review.disadvantages || '';
    this.reviewForm.querySelector('input[name="raw_rating"]').value = review.raw_rating || '';
    this.reviewForm.querySelector('input[name="rating"]').value = review.rating || '';
    this.reviewForm.querySelector('input[name="max_rating"]').value = review.max_rating || '';
    this.reviewForm.querySelector('input[name="normalized_rating"]').value = review.normalized_rating || '0';
  }

  async saveReview() {
    if (!this.reviewForm) return;

    const formData = new FormData(this.reviewForm);
    const reviewData = Object.fromEntries(formData.entries());
    
    // Очищаем данные - заменяем пустые строки на null для числовых полей
    const numericFields = ['importance', 'rating', 'max_rating', 'normalized_rating'];
    numericFields.forEach(field => {
      if (reviewData[field] === '' || reviewData[field] === undefined) {
        reviewData[field] = null;
      } else {
        reviewData[field] = Number(reviewData[field]);
      }
    });
    
    // Обрабатываем текстовые поля - заменяем null на пустые строки
    const textFields = ['source', 'text', 'advantages', 'disadvantages', 'raw_rating'];
    textFields.forEach(field => {
      if (reviewData[field] === null || reviewData[field] === undefined) {
        reviewData[field] = '';
      }
    });
    
    // Убираем review_id если он пустой
    if (reviewData.review_id === '') {
      delete reviewData.review_id;
    }
    
    // Преобразуем product_id в число
    if (reviewData.product_id) {
      reviewData.product_id = Number(reviewData.product_id);
    }
    
    // Преобразуем review_id в число для обновления
    if (reviewData.review_id) {
      reviewData.review_id = Number(reviewData.review_id);
    }
    
    // Убираем поля с null значениями для числовых полей, которые могут быть необязательными
    Object.keys(reviewData).forEach(key => {
      if (reviewData[key] === null && numericFields.includes(key)) {
        delete reviewData[key];
      }
    });
    
    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      alert('Нет CSRF токена! Невозможно сохранить.');
      return;
    }

    try {
      const url = '/api/review';
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-Token': csrf_token
        },
        body: JSON.stringify(reviewData),
        credentials: 'same-origin'
      });

      if (response.ok) {
        const result = await response.json().catch(() => null);
        
        if (result && result.id) {
          this.closeReviewModal();
          const newReviewId = result.id;
          
          // Этап 1: Проверяем текущие фильтры
          const filtersStatus = this.getCurrentFiltersStatus();
          
          this.goToLastPageAndHighlight(newReviewId);
          TableUtils.showToast('Отзыв успешно сохранен', { type: 'success' });
        } else {
          alert('Ошибка: отзыв не был сохранен. Проверьте данные и попробуйте снова.');
        }
      } else {
        const errorData = await response.json().catch(() => null);
        alert(errorData?.detail || ANALYZE_PRODUCT_CONFIG.MESSAGES.SAVE_ERROR);
      }
    } catch (error) {
      alert(ANALYZE_PRODUCT_CONFIG.MESSAGES.SAVE_ERROR);
    }
  }

  async deleteReview(reviewId) {
    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      alert('Нет CSRF токена! Невозможно удалить.');
      return;
    }

    try {
      const response = await fetch(`/api/review/${reviewId}/delete`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'X-CSRF-Token': csrf_token
        },
        credentials: 'same-origin'
      });

      if (response.ok) {
        TableUtils.fetchPage();
        TableUtils.showToast('Отзыв успешно удален', { type: 'success' });
      } else {
        const errorData = await response.json().catch(() => null);
        alert(errorData?.detail || ANALYZE_PRODUCT_CONFIG.MESSAGES.DELETE_ERROR);
      }
    } catch (error) {
      console.error('Delete review error:', error);
      alert(ANALYZE_PRODUCT_CONFIG.MESSAGES.DELETE_ERROR);
    }
  }

  async clearReviews() {
    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      alert('Нет CSRF токена! Невозможно очистить отзывы.');
      return;
    }

    try {
      const response = await fetch(`/api/review/clear/${this.productId}`, {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'X-CSRF-Token': csrf_token
        },
        credentials: 'same-origin'
      });

      if (response.ok) {
        TableUtils.fetchPage();
        TableUtils.showToast('Отзывы успешно очищены', { type: 'success' });
      } else {
        const errorData = await response.json().catch(() => null);
        alert(errorData?.detail || 'Ошибка при очистке отзывов');
      }
    } catch (error) {
      console.error('Clear reviews error:', error);
      alert('Ошибка при очистке отзывов');
    }
  }

  showUploadSection(event) {
    event.preventDefault();
    const uploadSection = document.getElementById('upload-section');
    if (uploadSection) {
      uploadSection.classList.remove('hidden');
      uploadSection.classList.add('block');
    }
  }

  hideUploadSection(event) {
    event.preventDefault();
    const uploadSection = document.getElementById('upload-section');
    if (uploadSection) {
      uploadSection.classList.add('hidden');
      uploadSection.classList.remove('block');
    }
  }

  async handleAnalyze(event) {
    event.preventDefault();
    
    try {
      const analyzeStatus = document.getElementById('analyze-status');
      analyzeStatus.textContent = "Анализируем отзывы...";
      analyzeStatus.style.color = "blue";
      
      this.analyzeButton.disabled = true;

      const promtId = document.getElementById("promt_id").value;
      
      // Используем TableUtils для получения фильтров
      const filters = TableUtils.getAllFiltersAndSort();
      filters.promt_id = promtId;

      Object.keys(filters).forEach(key => {
        // Преобразуем к числу если это числовое поле фильтра
        if (["promt_id", "importance", "normalized_rating_min", "normalized_rating_max"].includes(key)) {
          if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
            filters[key] = Number(filters[key]);
          }
        }
        // Теперь убираем всё, что не выбрано:
        if (
          filters[key] === "" ||
          filters[key] === undefined ||
          filters[key] === null ||
          (["promt_id", "importance", "normalized_rating_min", "normalized_rating_max"].includes(key) && filters[key] === 0)
        ) {
          delete filters[key];
        }
      });
      
      const payload = filters;

      const response = await fetch(`/analyze/${this.productId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRF-Token": getCSRFToken()
        },
        credentials: "same-origin",
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (!response.ok) {
          console.error("Ошибка FastAPI:", data.detail);
          throw new Error(data.detail || "Ошибка на сервере");
      }

      analyzeStatus.textContent = "Анализ завершён успешно!";
      analyzeStatus.style.color = "green";
      document.getElementById('analysis_result').value = data.result;
    } catch (error) {
      const analyzeStatus = document.getElementById('analyze-status');
      analyzeStatus.textContent = "Ошибка анализа: " + error.message;
      analyzeStatus.style.color = "red";
    } finally {
      this.analyzeButton.disabled = false;
    }
  }

  async handleFiles(fileList) {
    if (!fileList || fileList.length === 0) return;
    
    const statusDiv = document.getElementById('upload-status');
    statusDiv.classList.remove('hidden');
    statusDiv.innerHTML = `Обработка файлов...`;
    
    let overallHtml = '', totalUploaded = 0, totalRows = 0, totalEmpty = 0, errorFiles = 0;

    for (let file of fileList) {
      if (!isAllowedFile(file)) {
        overallHtml += `<div class="mb-2 p-2 border rounded bg-white">
          <b>Файл:</b> ${file.name}<br>
          <span class="text-red-600">Формат файла не поддерживается для загрузки отзывов.</span>
        </div>`; 
        errorFiles += 1; 
        continue;
      }
      
      const formData = new FormData();
      formData.append('file', file);
      const productId = this.productId;
      let fileHtml = `<div class="mb-2 p-2 border rounded bg-white"><b>Файл:</b> ${file.name}<br>`;
      
      try {
        const response = await fetch(`/parse-reviews-file/${productId}`, {
          method: 'POST', 
          body: formData, 
          credentials: 'include',
          headers: { "X-CSRF-Token": getCSRFToken() }
        });
        const data = await response.json();
        
        if (response.ok) {
          // Обновляем таблицу через TableUtils
          TableUtils.fetchPage();
        } else {
          alert("Ошибка загрузки файла: " + (data.detail || ""));
        }

        fileHtml += `Формат: <code>${file.type || file.name.split('.').pop().toUpperCase()}</code><br>`;
        if (data.errors && data.errors.length) {
          fileHtml += `<span class="text-red-600">Завершено с ошибками</span><br>`; 
          errorFiles += 1;
        } else {
          fileHtml += `<span class="text-green-600">Успешно!</span><br>`;
        }
        fileHtml += `Загружено строк: <b>${data.success_count}</b> из <b>${data.total_rows}</b><br>`;
        if (data.empty_rows) {
          fileHtml += `Пустых строк: <b>${data.empty_rows}</b><br>`;
        }
        if (data.errors && data.errors.length) {
          fileHtml += `<div class="text-red-600">Ошибки:<ul>`;
          data.errors.forEach(err => fileHtml += `<li class="mb-1" title="Исправьте по примеру в тексте ошибки">${err}</li>`);
          fileHtml += `</ul></div>`;
        }
        totalUploaded += data.success_count; 
        totalRows += data.total_rows; 
        totalEmpty += data.empty_rows;
      } catch (err) {
        fileHtml += `<span class="text-red-600">Ошибка загрузки: ${err}</span>`; 
        errorFiles += 1;
      }
      fileHtml += `</div>`; 
      overallHtml += fileHtml;
    }
    
    overallHtml = `<div class="mb-4 p-2 rounded bg-blue-50 border border-blue-200">
        <b>Всего файлов:</b> ${fileList.length} &nbsp;|&nbsp;
        <b>Импортировано строк:</b> ${totalUploaded} / ${totalRows}
        ${totalEmpty ? `&nbsp;|&nbsp;<b>Пустых строк:</b> ${totalEmpty}` : ""}
        ${errorFiles > 0 ? `<br><span class="text-red-600">Файлов с ошибками: ${errorFiles}</span>` : ""}
      </div>` + overallHtml;
    statusDiv.innerHTML = overallHtml;
  }

  highlightNewReview(reviewId) {
    // Проверяем, соответствует ли отзыв текущим фильтрам
    this.checkReviewVisibility(reviewId).then(result => {
      if (result.visible) {
        // Отзыв виден - выделяем его
        const newReviewRow = document.getElementById(`review-row-${reviewId}`);
        
        if (newReviewRow) {
          newReviewRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
          newReviewRow.classList.add('bg-blue-100');
          newReviewRow.classList.add('border-blue-300');
          newReviewRow.classList.add('shadow-md');
          newReviewRow.classList.add('z-10');
          
          // Убираем выделение через 3 секунды
          setTimeout(() => {
            newReviewRow.classList.remove('bg-blue-100', 'border-blue-300', 'shadow-md', 'z-10');
          }, 3000);
        } else {
          // Попробуем найти отзыв в карточках (мобильная версия)
          const reviewCard = document.querySelector(`[data-id="${reviewId}"]`);
          if (reviewCard) {
            reviewCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            reviewCard.classList.add('bg-blue-100', 'border-blue-300', 'shadow-md');
            setTimeout(() => {
              reviewCard.classList.remove('bg-blue-100', 'border-blue-300', 'shadow-md');
            }, 3000);
          }
        }
      } else {
        // Отзыв не соответствует фильтрам - уведомляем пользователя
        let message = 'Отзыв сохранен, но не отображается из-за текущих фильтров.';
        
        if (result.failedFilter) {
          const filterNames = {
            'importance': 'важности',
            'source': 'источника',
            'text': 'текста',
            'advantages': 'преимуществ',
            'disadvantages': 'недостатков',
            'normalized_rating_min': 'минимального рейтинга',
            'normalized_rating_max': 'максимального рейтинга'
          };
          
          const filterName = filterNames[result.failedFilter] || result.failedFilter;
          const filterResult = result.filterResults[result.failedFilter];
          
          if (filterResult) {
            if (result.failedFilter.includes('normalized_rating')) {
              message = `Отзыв сохранен, но не отображается из-за фильтра ${filterName}. `;
              message += `Рейтинг отзыва: ${filterResult.reviewValue}%, фильтр: ${filterResult.filterValue}%.`;
            } else if (result.failedFilter === 'importance') {
              message = `Отзыв сохранен, но не отображается из-за фильтра ${filterName}. `;
              message += `Значение отзыва: "${filterResult.reviewValue || 'пусто'}", фильтр: "${filterResult.filterValue}".`;
            } else {
              message = `Отзыв сохранен, но не отображается из-за фильтра ${filterName}. `;
              message += `В поле "${filterName}" не найдено: "${filterResult.filterValue}".`;
            }
          }
        }
        
        const resetButton = document.createElement('button');
        resetButton.textContent = 'Сбросить фильтры';
        resetButton.className = 'ml-2 px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600';
        resetButton.onclick = () => {
          this.resetFilters();
        };
        
        this.showCustomToast(message, resetButton, { 
          type: 'warning',
          duration: 8000 
        });
      }
    });
  }

  async checkReviewVisibility(reviewId) {
    try {
      // Получаем текущие фильтры
      const currentFilters = TableUtils.getAllFiltersAndSort();
      
      // Определяем активные фильтры (исключаем служебные)
      const activeFilters = {};
      const serviceFields = ['product_id', 'page', 'limit', 'sort_by', 'sort_dir'];
      
      for (const [key, value] of Object.entries(currentFilters)) {
        if (!serviceFields.includes(key) && value !== '' && value !== null && value !== undefined) {
          activeFilters[key] = value;
        }
      }
      
      // Если нет активных фильтров - отзыв виден
      if (Object.keys(activeFilters).length === 0) {
        return { visible: true, reason: 'no_filters' };
      }

      // Получаем данные отзыва для проверки соответствия фильтрам
      const response = await fetch(`/api/review/${reviewId}`);
      if (!response.ok) {
        return { visible: true, reason: 'fetch_error' };
      }

      const review = await response.json();
      
      // Проверяем соответствие каждому фильтру
      const filterResults = {};
      
      // Проверка importance
      if (activeFilters.importance !== undefined) {
        const filterValue = activeFilters.importance;
        const reviewValue = review.importance;
        const matches = reviewValue == filterValue;
        filterResults.importance = { filterValue, reviewValue, matches };
      }
      
      // Проверка source (поиск подстроки)
      if (activeFilters.source !== undefined) {
        const filterValue = activeFilters.source.toLowerCase();
        const reviewValue = (review.source || '').toLowerCase();
        const matches = reviewValue.includes(filterValue);
        filterResults.source = { filterValue, reviewValue, matches };
      }
      
      // Проверка text (поиск подстроки)
      if (activeFilters.text !== undefined) {
        const filterValue = activeFilters.text.toLowerCase();
        const reviewValue = (review.text || '').toLowerCase();
        const matches = reviewValue.includes(filterValue);
        filterResults.text = { filterValue, reviewValue, matches };
      }
      
      // Проверка advantages (поиск подстроки)
      if (activeFilters.advantages !== undefined) {
        const filterValue = activeFilters.advantages.toLowerCase();
        const reviewValue = (review.advantages || '').toLowerCase();
        const matches = reviewValue.includes(filterValue);
        filterResults.advantages = { filterValue, reviewValue, matches };
      }
      
      // Проверка disadvantages (поиск подстроки)
      if (activeFilters.disadvantages !== undefined) {
        const filterValue = activeFilters.disadvantages.toLowerCase();
        const reviewValue = (review.disadvantages || '').toLowerCase();
        const matches = reviewValue.includes(filterValue);
        filterResults.disadvantages = { filterValue, reviewValue, matches };
      }
      
      // Проверка normalized_rating_min
      if (activeFilters.normalized_rating_min !== undefined) {
        const filterValue = parseFloat(activeFilters.normalized_rating_min);
        const reviewValue = parseFloat(review.normalized_rating || 0);
        const matches = reviewValue >= filterValue;
        filterResults.normalized_rating_min = { filterValue, reviewValue, matches };
      }
      
      // Проверка normalized_rating_max
      if (activeFilters.normalized_rating_max !== undefined) {
        const filterValue = parseFloat(activeFilters.normalized_rating_max);
        const reviewValue = parseFloat(review.normalized_rating || 0);
        const matches = reviewValue <= filterValue;
        filterResults.normalized_rating_max = { filterValue, reviewValue, matches };
      }
      
      // Проверяем, все ли фильтры пройдены
      const allFiltersPassed = Object.values(filterResults).every(result => result.matches);
      
      if (allFiltersPassed) {
        return { visible: true, reason: 'filters_passed', filterResults };
      } else {
        // Находим первый непройденный фильтр для сообщения
        const failedFilter = Object.entries(filterResults).find(([key, result]) => !result.matches);
        const reason = failedFilter ? `filter_failed_${failedFilter[0]}` : 'filter_failed';
        return { visible: false, reason, filterResults, failedFilter: failedFilter?.[0] };
      }
      
    } catch (error) {
      return { visible: true, reason: 'error', error: error.message };
    }
  }

  resetFilters() {
    // Очищаем все поля фильтров
    const filterInputs = [
      '#tab_search_importance',
      '#tab_search_source', 
      '#tab_search_text',
      '#tab_search_advantages',
      '#tab_search_disadvantages',
      '#tab_search_normalized_rating',
      '#mob_search_importance',
      '#mob_search_source',
      '#mob_search_text', 
      '#mob_search_advantages',
      '#mob_search_disadvantages',
      '#mob_search_normalized_rating'
    ];
    
    filterInputs.forEach(selector => {
      const input = document.querySelector(selector);
      if (input) {
        input.value = '';
      }
    });
    
    // Сбрасываем сортировку
    TableUtils.setFilters({
      sort_by: '',
      sort_dir: 'asc',
      page: 1
    });
    
    // Обновляем таблицу
    TableUtils.fetchPage();
  }

  showCustomToast(message, button, options = {}) {
    const toast = document.createElement('div');
    toast.className = 'custom-toast flex items-center justify-between';
    toast.style.cssText = `
      position: fixed;
      left: 50%;
      bottom: 32px;
      transform: translateX(-50%);
      background: ${options.type === 'warning' ? '#f59e0b' : '#323A4B'};
      color: white;
      padding: 14px 32px;
      border-radius: 12px;
      font-size: 1rem;
      box-shadow: 0 4px 24px rgba(0,0,0,0.18);
      z-index: 9999;
      opacity: 0;
      transition: opacity 0.3s;
      max-width: 500px;
      white-space: nowrap;
    `;
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    toast.appendChild(messageSpan);
    toast.appendChild(button);
    
    document.body.appendChild(toast);
    
    setTimeout(() => { toast.style.opacity = 1; }, 10);
    setTimeout(() => {
      toast.style.opacity = 0;
      setTimeout(() => toast.remove(), 300);
    }, options.duration || 3500);
  }

  async goToLastPageAndHighlight(reviewId) {
    try {
      // Этап 4: Определяем правильную страницу для отзыва
      const pageResult = await this.findReviewPage(reviewId);
      
      if (pageResult.reason === 'found') {
        // Переходим на нужную страницу
        TableUtils.setFilters({ page: pageResult.page });
        
        // Обновляем таблицу
        await TableUtils.fetchPage();
        
        // Выделяем отзыв с небольшой задержкой для полной загрузки DOM
        setTimeout(() => {
          this.highlightNewReview(reviewId);
        }, 800);
      } else {
        // В случае ошибки просто выделяем отзыв на текущей странице
        setTimeout(() => {
          this.highlightNewReview(reviewId);
        }, 500);
      }
    } catch (error) {
      // В случае ошибки пытаемся выделить отзыв
      setTimeout(() => {
        this.highlightNewReview(reviewId);
      }, 500);
    }
  }

  // Метод для определения правильной страницы отзыва с учетом сортировки
  async findReviewPage(reviewId) {
    try {
      // Получаем текущие фильтры и сортировку
      const currentFilters = TableUtils.getAllFiltersAndSort();
      
      // Получаем данные отзыва
      const reviewResponse = await fetch(`/api/review/${reviewId}`);
      if (!reviewResponse.ok) {
        return { page: 1, reason: 'fetch_error' };
      }
      
      const review = await reviewResponse.json();
      
      // Формируем параметры запроса - только нужные фильтры и сортировка
      const queryParams = {
        product_id: currentFilters.product_id,
        page: 1,
        limit: 10000 // Большой лимит чтобы получить все отзывы
      };
      
      // Добавляем сортировку
      if (currentFilters.sort_by) {
        queryParams.sort_by = currentFilters.sort_by;
      }
      if (currentFilters.sort_dir) {
        queryParams.sort_dir = currentFilters.sort_dir;
      }
      
      // Добавляем только активные фильтры (исключаем служебные)
      const serviceFields = ['product_id', 'page', 'limit', 'sort_by', 'sort_dir'];
      for (const [key, value] of Object.entries(currentFilters)) {
        if (!serviceFields.includes(key) && value !== '' && value !== null && value !== undefined) {
          queryParams[key] = value;
        }
      }
      
      // Получаем все отзывы с текущими фильтрами
      const allReviewsResponse = await fetch('/analyze/data?' + new URLSearchParams(queryParams));
      
      if (!allReviewsResponse.ok) {
        return { page: 1, reason: 'fetch_error' };
      }
      
      const allReviewsData = await allReviewsResponse.json();
      const allReviews = allReviewsData.items || [];
      
      // Находим позицию нашего отзыва в отсортированном списке
      const reviewIndex = allReviews.findIndex(r => r.id == reviewId);
      
      if (reviewIndex === -1) {
        return { page: 1, reason: 'not_found' };
      }
      
      const reviewPosition = reviewIndex + 1; // Позиция с 1
      const pageLimit = currentFilters.limit || 10;
      const targetPage = Math.ceil(reviewPosition / pageLimit);
      
      return { 
        page: targetPage, 
        reason: 'found',
        position: reviewPosition,
        totalReviews: allReviews.length,
        pageLimit: pageLimit
      };
      
    } catch (error) {
      return { page: 1, reason: 'error', error: error.message };
    }
  }
}

// ====================
// === INIT ON LOAD ===
// ====================
document.addEventListener('DOMContentLoaded', function() {
  const manager = new AnalyzeProductManager();
  
  // Настройка обработчиков для загрузки файлов
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-upload');
  const fakeBrowse = document.getElementById('fake-browse');

  // Обработчик для кнопки выбора файла
  fakeBrowse?.addEventListener('click', () => fileInput.click());

  // Обработчики для drag & drop
  ['dragenter', 'dragover'].forEach(event => {
    dropZone?.addEventListener(event, (e) => {
      e.preventDefault(); 
      e.stopPropagation();
      dropZone.classList.add('bg-blue-100', 'border-blue-600');
    });
  });
  
  ['dragleave', 'drop'].forEach(event => {
    dropZone?.addEventListener(event, (e) => {
      e.preventDefault(); 
      e.stopPropagation();
      dropZone.classList.remove('bg-blue-100', 'border-blue-600');
    });
  });

  // Обработчик drop
  dropZone?.addEventListener('drop', (e) => {
    e.preventDefault();
    manager.handleFiles(e.dataTransfer.files);
  });
  
  // Обработчик выбора файла
  fileInput?.addEventListener('change', () => manager.handleFiles(fileInput.files));
});

// ================== UPLOADING FILES TOGGLE ==================
AnalyzeProductManager.prototype.initUploadingFiles = function() {
  // Инициализация: скрываем блок и показываем первую иконку
  if (this.uploadingFiles) {
    this.uploadingFiles.style.display = 'none';
    this.uploadingFiles.style.opacity = '0';
    this.uploadingFiles.style.maxHeight = '0';
    this.uploadingFiles.style.overflow = 'hidden';
    this.uploadingFiles.style.transition = 'all 0.3s ease-in-out';
  }
  
  // Показываем первую иконку (когда блок скрыт)
  this.updateUploadingFilesIcon(false);
};

AnalyzeProductManager.prototype.toggleUploadingFiles = function(event) {
  event.preventDefault();
  
  if (this.isUploadingFilesVisible) {
    this.hideUploadingFiles();
  } else {
    this.showUploadingFiles();
  }
};

AnalyzeProductManager.prototype.showUploadingFiles = function() {
  if (!this.uploadingFiles) return;
  
  this.isUploadingFilesVisible = true;
  
  // Показываем блок
  this.uploadingFiles.style.display = 'block';
  
  // Небольшая задержка для корректной анимации
  setTimeout(() => {
    this.uploadingFiles.style.opacity = '1';
    this.uploadingFiles.style.maxHeight = '1000px'; // Достаточно большое значение
  }, 10);
  
  // Меняем иконку на вторую (когда блок показан)
  this.updateUploadingFilesIcon(true);
};

AnalyzeProductManager.prototype.hideUploadingFiles = function() {
  if (!this.uploadingFiles) return;
  
  this.isUploadingFilesVisible = false;
  
  // Скрываем блок
  this.uploadingFiles.style.opacity = '0';
  this.uploadingFiles.style.maxHeight = '0';
  
  // Полностью скрываем после завершения анимации
  setTimeout(() => {
    this.uploadingFiles.style.display = 'none';
  }, 300);
  
  // Меняем иконку на первую (когда блок скрыт)
  this.updateUploadingFilesIcon(false);
};

AnalyzeProductManager.prototype.updateUploadingFilesIcon = function(isVisible) {
  if (!this.uploadingFilesBtn) return;
  
  const svgElements = this.uploadingFilesBtn.querySelectorAll('svg');
  if (svgElements.length >= 2) {
    // Первая иконка (когда блок скрыт) - показываем
    svgElements[0].style.display = isVisible ? 'none' : 'block';
    // Вторая иконка (когда блок показан) - показываем
    svgElements[1].style.display = isVisible ? 'block' : 'none';
  }
};

// ================== ANALYSIS RESULT IMPROVEMENTS ==================
AnalyzeProductManager.prototype.initAnalysisResult = function() {
  const analysisResult = document.getElementById('analysis_result');
  if (!analysisResult) return;

  // Автоматическое изменение высоты при вводе текста
  this.autoResizeTextarea(analysisResult);
  
  // Добавляем обработчики для лучшего UX
  analysisResult.addEventListener('input', () => {
    this.autoResizeTextarea(analysisResult);
  });

  // Улучшенная обработка resize для мобильных устройств
  this.initMobileResize(analysisResult);
  
  // Инициализация при загрузке
  this.autoResizeTextarea(analysisResult);
};

AnalyzeProductManager.prototype.autoResizeTextarea = function(textarea) {
  // Сбрасываем высоту для корректного расчета
  textarea.style.height = 'auto';
  
  // Устанавливаем новую высоту на основе содержимого
  const scrollHeight = textarea.scrollHeight;
  const minHeight = parseInt(getComputedStyle(textarea).minHeight) || 120;
  const maxHeight = parseInt(getComputedStyle(textarea).maxHeight) || 600;
  
  const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
  textarea.style.height = newHeight + 'px';
};

AnalyzeProductManager.prototype.initMobileResize = function(textarea) {
  let isResizing = false;
  let startY = 0;
  let startHeight = 0;

  const container = textarea.closest('.analysis-result-container');
  if (!container) return;

  // Создаем кастомную область для resize на мобильных
  const resizeHandle = document.createElement('div');
  resizeHandle.className = 'mobile-resize-handle';
  resizeHandle.innerHTML = `
    <div class="resize-indicator">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M2 14L14 2M2 2L14 14" stroke="#A3B8F8" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </div>
  `;
  container.appendChild(resizeHandle);

  // Обработчики для touch событий
  resizeHandle.addEventListener('touchstart', (e) => {
    e.preventDefault();
    isResizing = true;
    startY = e.touches[0].clientY;
    startHeight = textarea.offsetHeight;
    resizeHandle.style.background = 'rgba(163, 184, 248, 0.3)';
  });

  resizeHandle.addEventListener('touchmove', (e) => {
    if (!isResizing) return;
    e.preventDefault();
    
    const deltaY = e.touches[0].clientY - startY;
    const newHeight = Math.max(120, Math.min(600, startHeight + deltaY));
    
    textarea.style.height = newHeight + 'px';
  });

  resizeHandle.addEventListener('touchend', () => {
    isResizing = false;
    resizeHandle.style.background = 'rgba(163, 184, 248, 0.1)';
  });

  // Обработчики для mouse событий (десктоп)
  resizeHandle.addEventListener('mousedown', (e) => {
    e.preventDefault();
    isResizing = true;
    startY = e.clientY;
    startHeight = textarea.offsetHeight;
    resizeHandle.style.background = 'rgba(163, 184, 248, 0.3)';
  });

  document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    
    const deltaY = e.clientY - startY;
    const newHeight = Math.max(120, Math.min(600, startHeight + deltaY));
    
    textarea.style.height = newHeight + 'px';
  });

  document.addEventListener('mouseup', () => {
    if (isResizing) {
      isResizing = false;
      resizeHandle.style.background = 'rgba(163, 184, 248, 0.1)';
    }
  });
};

// ================== LEGACY FUNCTIONS ===
// =====================
// Оставляем старые функции для совместимости, но они теперь используют TableUtils

function getReviewFilters() {
  const filters = TableUtils.getAllFiltersAndSort();
  filters.product_id = document.getElementById('analyze-button')?.dataset.productId;
  return new URLSearchParams(filters).toString();
}

function fetchPage(highlightId = null) {
  TableUtils.fetchPage();
}

function updateReviewsTable(reviews, highlightId) {
  // Эта функция теперь не нужна, так как TableUtils сам обновляет таблицу
  console.log('updateReviewsTable called, but TableUtils handles this automatically');
}

// Остальные функции из старого файла можно оставить для совместимости
// или постепенно перенести их логику в AnalyzeProductManager



// - HELPs - //
const analyzeHelpBtn = document.getElementById('analyze-help');
const analyzeTooltip = document.getElementById('analyze-tooltip');
const downloadHelpBtn = document.getElementById('download-help');
const downloadTooltip = document.getElementById('download-tooltip');
const toggleHelpBtn = document.getElementById('toggle-help');
const toggleTooltip = document.getElementById('toggle-tooltip');

// Основная подсказка
analyzeHelpBtn.addEventListener('click', function(e) {
  e.preventDefault();
  analyzeTooltip.classList.toggle('hidden');
  downloadTooltip.classList.add('hidden');
  toggleTooltip.classList.add('hidden');
});
downloadHelpBtn.addEventListener('click', function(e) {
  e.preventDefault();
  analyzeTooltip.classList.add('hidden');
  downloadTooltip.classList.toggle('hidden');
  toggleTooltip.classList.add('hidden');
});
toggleHelpBtn.addEventListener('click', function(e) {
  e.preventDefault();
  analyzeTooltip.classList.add('hidden');
  downloadTooltip.classList.add('hidden');
  toggleTooltip.classList.toggle('hidden');
});

// Скрывать обе при клике вне
document.addEventListener('click', function(e) {
  if (
    !analyzeHelpBtn.contains(e.target) && !analyzeTooltip.contains(e.target) &&
    !downloadHelpBtn.contains(e.target) && !downloadTooltip.contains(e.target) &&
    !toggleHelpBtn.contains(e.target) && !toggleTooltip.contains(e.target)
  ) {
    analyzeTooltip.classList.add('hidden');
    downloadTooltip.classList.add('hidden');
    toggleTooltip.classList.add('hidden');
  }
});


// ================== MODAL HANDLERS ==================
document.addEventListener('DOMContentLoaded', function () {
  const rawRatingInput = document.getElementById('raw_rating');
  const ratingInput = document.getElementById('rating');
  const maxRatingInput = document.getElementById('max_rating');
  const normalizedInput = document.getElementById('normalized_rating');

  function updateNormalized() {
    // Получаем значения
    const rating = parseFloat(ratingInput.value);
    const maxRating = parseFloat(maxRatingInput.value);

    // Формируем строку вида "rating/maxRating" или "0/0" если пусто/NaN
    const ratingStr = !isNaN(rating) ? rating.toString() : "0";
    const maxRatingStr = !isNaN(maxRating) ? maxRating.toString() : "0";
    rawRatingInput.value = ratingStr + "/" + maxRatingStr;

    // Считаем нормализованный рейтинг
    if (!isNaN(rating) && !isNaN(maxRating) && maxRating > 0) {
        normalizedInput.value = Math.round((rating / maxRating) * 100);
    } else {
        normalizedInput.value = 0;
    }
  }

  ratingInput?.addEventListener('blur', updateNormalized);
  maxRatingInput?.addEventListener('blur', updateNormalized);

  // При загрузке формы также считаем
  updateNormalized();
});

// Resizable textarea functionality
class ResizableTextarea {
  constructor(textareaId, handleSelector) {
    this.textarea = document.getElementById(textareaId);
    this.handle = document.querySelector(handleSelector);
    this.container = this.textarea.parentElement;
    
    if (!this.textarea || !this.handle) {
      console.warn('ResizableTextarea: Required elements not found');
      return;
    }
    
    this.isResizing = false;
    this.startY = 0;
    this.startHeight = 0;
    this.minHeight = 120;
    this.maxHeight = 800;
    
    this.init();
  }
  
  init() {
    // Автоматическое изменение высоты при вводе
    this.textarea.addEventListener('input', () => this.autoResize());
    
    // Инициализация высоты
    this.autoResize();
    
    // Обработчики для ручного изменения размера (мышь)
    this.handle.addEventListener('mousedown', (e) => this.startResize(e));
    document.addEventListener('mousemove', (e) => this.resize(e));
    document.addEventListener('mouseup', () => this.stopResize());
    
    // Обработчики для touch событий (мобильные устройства)
    this.handle.addEventListener('touchstart', (e) => this.startResize(e.touches[0]));
    document.addEventListener('touchmove', (e) => this.resize(e.touches[0]));
    document.addEventListener('touchend', () => this.stopResize());
    
    // Предотвращение выделения текста при перетаскивании
    this.handle.addEventListener('selectstart', (e) => e.preventDefault());
    this.handle.addEventListener('dragstart', (e) => e.preventDefault());
    
    // Предотвращение контекстного меню на handle
    this.handle.addEventListener('contextmenu', (e) => e.preventDefault());
  }
  
  autoResize() {
    // Создаем временный элемент для измерения высоты
    const temp = document.createElement('div');
    const computedStyle = getComputedStyle(this.textarea);
    
    temp.style.cssText = `
      position: absolute;
      top: -9999px;
      left: -9999px;
      width: ${this.textarea.offsetWidth}px;
      font-family: ${computedStyle.fontFamily};
      font-size: ${computedStyle.fontSize};
      font-weight: ${computedStyle.fontWeight};
      line-height: ${computedStyle.lineHeight};
      padding: ${computedStyle.padding};
      border: ${computedStyle.border};
      box-sizing: border-box;
      white-space: pre-wrap;
      word-wrap: break-word;
      overflow-wrap: break-word;
      min-height: ${this.minHeight}px;
    `;
    
    // Используем value или placeholder
    const content = this.textarea.value || this.textarea.placeholder || '';
    temp.textContent = content;
    
    document.body.appendChild(temp);
    const scrollHeight = temp.scrollHeight;
    document.body.removeChild(temp);
    
    // Устанавливаем новую высоту с ограничениями
    const newHeight = Math.max(this.minHeight, Math.min(this.maxHeight, scrollHeight));
    
    // Обновляем высоту только если она изменилась
    const currentHeight = parseInt(this.textarea.style.height) || this.textarea.offsetHeight;
    if (Math.abs(newHeight - currentHeight) > 1) {
      this.textarea.style.height = `${newHeight}px`;
    }
  }
  
  startResize(e) {
    e.preventDefault();
    this.isResizing = true;
    this.startY = e.clientY;
    this.startHeight = this.textarea.offsetHeight;
    
    this.container.classList.add('resizing');
    document.body.style.cursor = 'ns-resize';
    document.body.style.userSelect = 'none';
  }
  
  resize(e) {
    if (!this.isResizing) return;
    
    e.preventDefault();
    
    const deltaY = e.clientY - this.startY;
    const newHeight = Math.max(this.minHeight, Math.min(this.maxHeight, this.startHeight + deltaY));
    
    this.textarea.style.height = `${newHeight}px`;
  }
  
  stopResize() {
    if (!this.isResizing) return;
    
    this.isResizing = false;
    this.container.classList.remove('resizing');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
  
  // Методы для управления состоянием загрузки
  showLoading() {
    this.container.classList.add('loading');
    this.textarea.disabled = true;
  }
  
  hideLoading() {
    this.container.classList.remove('loading');
    this.textarea.disabled = false;
  }
  
  // Метод для программного изменения высоты
  setHeight(height) {
    const newHeight = Math.max(this.minHeight, Math.min(this.maxHeight, height));
    this.textarea.style.height = `${newHeight}px`;
  }
  
  // Метод для получения текущей высоты
  getHeight() {
    return this.textarea.offsetHeight;
  }
  
  // Метод для сброса к минимальной высоте
  resetHeight() {
    this.setHeight(this.minHeight);
  }
}

// Инициализация resizable textarea при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  try {
    // Инициализация resizable textarea
    const resizableTextarea = new ResizableTextarea('analysis_result', '.resize-handle');
    
    // Обработчик изменения размера окна для пересчета высоты (с debounce)
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (resizableTextarea && resizableTextarea.textarea) {
          resizableTextarea.autoResize();
        }
      }, 100);
    });
    
    // Сохраняем ссылку на глобальный объект для отладки
    window.resizableTextarea = resizableTextarea;
    
  } catch (error) {
    console.error('Error initializing resizable textarea:', error);
  }
});