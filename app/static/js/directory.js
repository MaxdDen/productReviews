// ====================
// === CONSTANTS =======
// ====================
const DIRECTORY_CONFIG = {
  MODAL_SELECTORS: {
    modal: 'directory-modal',
    form: 'directory-modal-form',
    title: 'modal-title',
    name: 'modal-name',
    description: 'modal-description',
    id: 'modal-item-id',
    error: 'modal-error',
    closeBtn: 'close-modal',
    openBtn: 'open-create-modal'
  },
  MESSAGES: {
    ADD_TITLE: 'Добавить новый элемент',
    EDIT_TITLE: 'Редактировать элемент',
    DELETE_CONFIRM: 'Удалить этот элемент?',
    NO_CSRF: 'Нет CSRF токена!',
    NETWORK_ERROR: 'Сетевая ошибка или не удалось обработать ответ.',
    DELETE_ERROR_NETWORK: 'Сетевая ошибка или не удалось обработать ответ при удалении.',
    NO_ITEMS: 'Нет товаров'
  }
};

const directoryName = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.openBtn)?.dataset.directoryName;

// ====================
// === UTILS ===========
// ====================
function formatErrorMessage(errorData, defaultMessage) {
  if (errorData?.detail) {
    if (Array.isArray(errorData.detail)) {
      return errorData.detail.map(err => {
        const field = Array.isArray(err.loc) ? err.loc.join(' -> ') : 'Field';
        return `${field}: ${err.msg}`;
      }).join('\n');
    }
    return errorData.detail;
  }
  return defaultMessage;
}

// ====================
// === RENDER FUNCTIONS ===
// ====================
function renderProductCards(items, cardsContainer) {
    if (!cardsContainer) {
      console.warn('[renderProductCards] Нет контейнера для карточек');
      return;
    }
    if (!items || !items.length) {
      cardsContainer.innerHTML = '<div class="text-center text-gray-400">Нет элементов</div>';
      return;
    }
    cardsContainer.innerHTML = '';
    items.forEach(item => {
      cardsContainer.innerHTML += `
        <div class="card w-full bg-white rounded-xl shadow-custom shadow-[0px_2px_6px_0px_rgba(0,0,0,0.25)]" data-id="${item.id}">
            <div class="font-semibold text-sm text-white leading-none tracking-normal align-middle p-[10px] mb-[4px] bg-[#7D94CF]">${directoryName.charAt(0).toUpperCase() + directoryName.slice(1)}:</div>
            <div class="text-sm text-gray-700 mb-[4px] p-[10px] line-clamp-2">${item.name || ''}</div>
            <div class="font-semibold text-sm text-white leading-none tracking-normal align-middle p-[10px] mb-[4px] bg-[#7D94CF]">Description:</div>
            <div class="text-sm text-gray-700 mb-[4px] p-[10px] line-clamp-2">${item.description || ''}</div>
            <div class="card-arrow flex justify-end p-[10px]">
            <svg width="14" height="8" viewBox="0 0 14 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12.8346 1.25L7.0013 6.75L6.16797 5.96429M1.16797 1.25L3.11214 3.08333" stroke="#1F2125" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            </div>
            <div class="actions flex items-center justify-end gap-2 mt-4 p-[10px] md:mt-0 md:right-4 md:bottom-4">
            <button class="edit-item-btn rounded-full hover:bg-gray-200 transition p-1" title="Edit" data-id="${item.id}" data-name="${item.name}" data-description="${item.description || ''}">
                <svg width="24" height="24" viewBox="0 0 35 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="0.5" y="1" width="34" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                <path d="M18.9769 13.0492C18.9769 13.0492 19.0487 14.2805 20.135 15.3661C21.2212 16.4523 22.4519 16.5248 22.4519 16.5248L23.0312 15.9455C23.4921 15.4846 23.7511 14.8594 23.7511 14.2076C23.7511 13.5558 23.4921 12.9307 23.0312 12.4698C22.5704 12.0089 21.9452 11.75 21.2934 11.75C20.6416 11.75 20.0165 12.0089 19.5556 12.4698L18.9762 13.0492L17.5012 14.5242M22.4519 16.5242L19.1644 19.813L17.2262 21.7498L17.1262 21.8505C16.765 22.2111 16.5844 22.3917 16.3856 22.5467C16.151 22.7296 15.8972 22.8865 15.6287 23.0148C15.4012 23.123 15.1594 23.2036 14.675 23.3648L12.6244 24.0486M12.6244 24.0486L12.1231 24.2161C12.0063 24.2553 11.8808 24.2611 11.7609 24.2329C11.6409 24.2047 11.5312 24.1435 11.444 24.0564C11.3569 23.9693 11.2958 23.8595 11.2676 23.7396C11.2394 23.6196 11.2452 23.4942 11.2844 23.3773L11.4519 22.8761M12.6244 24.0486L11.4519 22.8761M11.4519 22.8761L12.1356 20.8255C12.2969 20.3411 12.3775 20.0992 12.4856 19.8717C12.6144 19.6021 12.7704 19.3498 12.9537 19.1148C13.1087 18.9161 13.2894 18.7355 13.65 18.3748L15.3137 16.7117" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
            </button>
            <button class="delete-item-btn rounded-full hover:bg-red-100 transition p-1" title="Delete" data-directory="${directoryName}" data-id="${item.id}">
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
      `;
    });
    //setupCardActivation();
}
  
TableUtils.init({
    tableSelector: '#directory-table',
    tbodySelector: '#directory-tbody',
    filterRowSelector: '#tab_search',
    filterInputs: [
      '#tab_search_name',
      '#mob_search_name',
      '#tab_search_description',
      '#mob_search_description'
    ],
    filterKeys: ['name', 'description'], // Ключи фильтров для справочников
    mobileFilterInputs: ['mob_search_name', 'mob_search_description'], // Мобильные фильтры
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
    mobilePaginationInfoSelector: '#mobile-pagination-info',
    mobilePaginationControlsSelector: '#mobile-pagination-controls',
    mobilePaginationContainerSelector: '#mobile-pagination',
    mobileCardsContainerSelector: '#items-cards',
    defaultSortBy: 'name',
    defaultSortDir: 'asc',
    dataUrl: `/directory/${directoryName}/data`,
    renderRow: function(item) {
        return `
            <tr class="align-middle border-b border-gray-200 table-row cursor-pointer">
                <td class="w-1/3 p-[5px] align-middle font-semibold text-gray-900">
                    <div class="line-clamp-2">${item.name}</div>
                </td>
                <td class="w-2/3 p-[5px] align-middle text-gray-700">
                    <div class="line-clamp-2">${item.description || ''}</div>
                </td>
                <td class="w-[120px] p-[5px] align-middle">
                    <div class="flex items-center justify-center gap-[5px]">
                        <button class="edit-item-btn rounded-full hover:bg-gray-200 transition p-1" title="Edit"
                                data-id="${item.id}"
                                data-name="${item.name}"
                                data-description="${item.description || ''}">
                            <svg width="24" height="24" viewBox="0 0 35 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <rect x="0.5" y="1" width="34" height="34" rx="9.5" stroke="#6B6397" stroke-opacity="0.2"/>
                                <path d="M18.9769 13.0492C18.9769 13.0492 19.0487 14.2805 20.135 15.3661C21.2212 16.4523 22.4519 16.5248 22.4519 16.5248L23.0312 15.9455C23.4921 15.4846 23.7511 14.8594 23.7511 14.2076C23.7511 13.5558 23.4921 12.9307 23.0312 12.4698C22.5704 12.0089 21.9452 11.75 21.2934 11.75C20.6416 11.75 20.0165 12.0089 19.5556 12.4698L18.9762 13.0492L17.5012 14.5242M22.4519 16.5242L19.1644 19.813L17.2262 21.7498L17.1262 21.8505C16.765 22.2111 16.5844 22.3917 16.3856 22.5467C16.151 22.7296 15.8972 22.8865 15.6287 23.0148C15.4012 23.123 15.1594 23.2036 14.675 23.3648L12.6244 24.0486M12.6244 24.0486L12.1231 24.2161C12.0063 24.2553 11.8808 24.2611 11.7609 24.2329C11.6409 24.2047 11.5312 24.1435 11.444 24.0564C11.3569 23.9693 11.2958 23.8595 11.2676 23.7396C11.2394 23.6196 11.2452 23.4942 11.2844 23.3773L11.4519 22.8761M12.6244 24.0486L11.4519 22.8761M11.4519 22.8761L12.1356 20.8255C12.2969 20.3411 12.3775 20.0992 12.4856 19.8717C12.6144 19.6021 12.7704 19.3498 12.9537 19.1148C13.1087 18.9161 13.2894 18.7355 13.65 18.3748L15.3137 16.7117" stroke="#6B6397" stroke-width="1.2" stroke-linecap="round"/>
                            </svg>
                        </button>
                        <button class="delete-item-btn rounded-full hover:bg-red-100 transition p-1" title="Delete"
                                data-directory="${directoryName}"
                                data-id="${item.id}">
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
    },
    renderCards: renderProductCards,
    cardsContainerSelector: '#items-cards',
    defaultFilters: {
      page: 1,
      limit: 10,
      sort_by: 'name',
      sort_dir: 'asc'
    },
    afterUpdateTable: function(data) {
      const params = new URLSearchParams(window.location.search);
      const highlightId = params.get('highlight_id');
      const newCreated = params.get('new_created');
      let found = false;
    
      if (highlightId) {
        const row = document.getElementById(`item-row-${highlightId}`);
        const card = document.querySelector(`#items-cards .card[data-id='${highlightId}']`);
    
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
      }
    
      if (newCreated && highlightId && !found) {
        TableUtils.showToast('Созданный элемент не соответствует текущим фильтрам. Измените фильтры, чтобы увидеть его.');
      }
    }
});



// - HELPs - //
const toggleHelpBtn = document.getElementById('toggle-help');
const toggleTooltip = document.getElementById('toggle-tooltip');

// Основная подсказка
toggleHelpBtn.addEventListener('click', function(e) {
  e.preventDefault();
  toggleTooltip.classList.toggle('hidden');
  tableActionsTooltip.classList.add('hidden'); // скрыть вторую, если вдруг открыта
});

// Скрывать обе при клике вне
document.addEventListener('click', function(e) {
  if (
    !toggleHelpBtn.contains(e.target) && !toggleTooltip.contains(e.target)
  ) {
    toggleTooltip.classList.add('hidden');
  }
});




// ====================
// === MODAL MANAGER ===
// ====================
class DirectoryModalManager {
  constructor() {
    this.modal = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.modal);
    this.form = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.form);
    this.modalTitle = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.title);
    this.modalName = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.name);
    this.modalDesc = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.description);
    this.modalId = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.id);
    this.modalError = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.error);
    this.closeModalBtn = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.closeBtn);
    this.openCreateBtn = document.getElementById(DIRECTORY_CONFIG.MODAL_SELECTORS.openBtn);
    
    this.init();
  }

  init() {
    if (!this.modal || !this.form) return;
    
    this.bindEvents();
  }

  bindEvents() {
    this.openCreateBtn?.addEventListener('click', () => this.openCreateModal());
    this.closeModalBtn?.addEventListener('click', () => this.closeModal());
    
    document.getElementById('directory-tbody')?.addEventListener('click', (event) => {
      this.handleTableClick(event);
    });
    
    // Обработчик кликов для карточек
    document.getElementById('items-cards')?.addEventListener('click', (event) => {
      this.handleCardsClick(event);
    });
    
    this.form?.addEventListener('submit', (event) => this.handleSubmit(event));
  }

  openCreateModal() {
    this.modalTitle.innerText = DIRECTORY_CONFIG.MESSAGES.ADD_TITLE;
    this.clearForm();
    this.showModal();
  }

  openEditModal(id, name, description) {
    this.modalTitle.innerText = DIRECTORY_CONFIG.MESSAGES.EDIT_TITLE;
    this.modalName.value = name || '';
    this.modalDesc.value = description || '';
    this.modalId.value = id || '';
    this.modalError.innerText = '';
    this.showModal();
  }

  clearForm() {
    this.modalName.value = '';
    this.modalDesc.value = '';
    this.modalId.value = '';
    this.modalError.innerText = '';
  }

  showModal() {
    this.modal.classList.remove('hidden');
  }

  closeModal() {
    this.modal.classList.add('hidden');
  }

  handleTableClick(event) {
    const editBtn = event.target.closest('.edit-item-btn');
    if (editBtn) {
      const { id, name, description } = editBtn.dataset;
      this.openEditModal(id, name, description);
      return;
    }

    const deleteBtn = event.target.closest('.delete-item-btn');
    if (deleteBtn) {
      this.handleDelete(deleteBtn);
    }
  }

  handleCardsClick(event) {
    const editBtn = event.target.closest('.edit-item-btn');
    if (editBtn) {
      const { id, name, description } = editBtn.dataset;
      this.openEditModal(id, name, description);
      return;
    }

    const deleteBtn = event.target.closest('.delete-item-btn');
    if (deleteBtn) {
      this.handleDelete(deleteBtn);
    }
  }

  async handleDelete(deleteBtn) {
    const itemId = deleteBtn.dataset.id;
    const directoryNameSingular = deleteBtn.dataset.directory;

    if (!confirm(DIRECTORY_CONFIG.MESSAGES.DELETE_CONFIRM)) return;

    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      alert(`${DIRECTORY_CONFIG.MESSAGES.NO_CSRF} Невозможно удалить.`);
      return;
    }

    try {
      const response = await fetch(`/api/${directoryNameSingular}/${itemId}`, {
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
        alert(formatErrorMessage(errorData, `Ошибка при удалении: ${response.status} ${response.statusText}`));
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert(DIRECTORY_CONFIG.MESSAGES.DELETE_ERROR_NETWORK);
    }
  }

  async handleSubmit(event) {
    event.preventDefault();
    this.modalError.innerText = '';
    
    const itemId = this.modalId.value;
    const name = this.modalName.value.trim();
    const description = this.modalDesc.value.trim();
    
    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      this.modalError.innerText = DIRECTORY_CONFIG.MESSAGES.NO_CSRF;
      return;
    }

    const directoryNameSingular = this.openCreateBtn.dataset.directoryName;
    const payload = { name, description };
    
    const url = itemId 
      ? `/api/${directoryNameSingular}/${itemId}`
      : `/api/${directoryNameSingular}/`;
    const method = itemId ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'X-CSRF-Token': csrf_token,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        this.closeModal();
        TableUtils.fetchPage();
      } else {
        const errorData = await response.json().catch(() => null);
        this.modalError.innerText = formatErrorMessage(errorData, `Ошибка: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Submit error:', error);
      this.modalError.innerText = DIRECTORY_CONFIG.MESSAGES.NETWORK_ERROR;
    }
  }
}

// ====================
// === INITIALIZATION ===
// ====================
document.addEventListener('DOMContentLoaded', () => {
  new DirectoryModalManager();
});

