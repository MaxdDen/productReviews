// ================== GLOBAL STATE ==================
let sortBy = 'id';
let sortDir = 'asc';
let currentPage = 1;

// --- DOM Elements ---
const pageLimitSelect = document.getElementById('page-limit-select');
const tableReviewsTBody = document.getElementById('reviews-tbody');
const pagDiv = document.getElementById('pagination-controls');
const pagInfo = document.getElementById('pagination-info');
const analyzeButton = document.getElementById('analyze-button');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-upload');
const fakeBrowse = document.getElementById('fake-browse');
const statusDiv = document.getElementById('upload-status');
const filterRow = document.getElementById('tab_search');
const filterHint = document.getElementById('filter-hint');
const analyzeStatus = document.getElementById('analyze-status');
const toggleFilterBtn = document.getElementById('toggle-filter-row');
const resetSortBtn = document.getElementById('reset-sort-btn');

// --- Range-slider DOM ---
const minRange = document.getElementById('min-range');
const maxRange = document.getElementById('max-range');
const minValue = document.getElementById('min-value');
const maxValue = document.getElementById('max-value');
const sliderTrack = document.getElementById('slider-track');
const clickArea = document.querySelector('.slider-click-area');
const sliderRoot = document.getElementById('range-slider-root');
const rangeSliderBtn = document.getElementById('range-slider-btn');
const minGap = 1, sliderMax = 100, sliderMin = 0; // Для normalized_rating (0–100)
let ratingFilterActive = false;


// --- Filter Inputs ---
const filterInputs = [
  'tab_search_importance', 'tab_search_source', 'tab_search_text', 'tab_search_advantages', 'tab_search_disadvantages'
].map(id => document.getElementById(id));

// ================== UTILS ==================
function isAllowedFile(file) {
  const allowedExtensions = ['csv', 'json', 'xlsx'];
  const ext = file.name.split('.').pop().toLowerCase();
  return allowedExtensions.includes(ext);
}
function toNumberOrNull(val) {
  return val === "" || val === undefined || val === null ? null : Number(val);
}

// ================== FILE UPLOAD ==================
fakeBrowse.addEventListener('click', () => fileInput.click());

['dragenter', 'dragover'].forEach(event => {
  dropZone.addEventListener(event, (e) => {
    e.preventDefault(); e.stopPropagation();
    dropZone.classList.add('bg-blue-100', 'border-blue-600');
  });
});
['dragleave', 'drop'].forEach(event => {
  dropZone.addEventListener(event, (e) => {
    e.preventDefault(); e.stopPropagation();
    dropZone.classList.remove('bg-blue-100', 'border-blue-600');
  });
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', () => handleFiles(fileInput.files));

document.getElementById('clear-upload-status').addEventListener('click', () => {
  statusDiv.innerHTML = '';
  fileInput.value = '';
});

async function handleFiles(fileList) {
  if (!fileList || fileList.length === 0) return;
  statusDiv.classList.remove('hidden');
  statusDiv.innerHTML = `Обработка файлов...`;
  let overallHtml = '', totalUploaded = 0, totalRows = 0, totalEmpty = 0, errorFiles = 0;

  for (let file of fileList) {
    if (!isAllowedFile(file)) {
      overallHtml += `<div class="mb-2 p-2 border rounded bg-white">
        <b>Файл:</b> ${file.name}<br>
        <span class="text-red-600">Формат файла не поддерживается для загрузки отзывов.</span>
      </div>`; errorFiles += 1; continue;
    }
    const formData = new FormData();
    formData.append('file', file);
    const productId = analyzeButton.dataset.productId;
    let fileHtml = `<div class="mb-2 p-2 border rounded bg-white"><b>Файл:</b> ${file.name}<br>`;
    try {
      const response = await fetch(`/parse-reviews-file/${productId}`, {
        method: 'POST', body: formData, credentials: 'include',
        headers: { "X-CSRF-Token": getCSRFToken() }
      });
      const data = await response.json();
      if (response.ok) fetchPage();
      else alert("Ошибка загрузки файла: " + (data.detail || ""));

      fileHtml += `Формат: <code>${file.type || file.name.split('.').pop().toUpperCase()}</code><br>`;
      if (data.errors && data.errors.length) {
        fileHtml += `<span class="text-red-600">Завершено с ошибками</span><br>`; errorFiles += 1;
      } else fileHtml += `<span class="text-green-600">Успешно!</span><br>`;
      fileHtml += `Загружено строк: <b>${data.success_count}</b> из <b>${data.total_rows}</b><br>`;
      if (data.empty_rows) fileHtml += `Пустых строк: <b>${data.empty_rows}</b><br>`;
      if (data.errors && data.errors.length) {
        fileHtml += `<div class="text-red-600">Ошибки:<ul>`;
        data.errors.forEach(err => fileHtml += `<li class="mb-1" title="Исправьте по примеру в тексте ошибки">${err}</li>`);
        fileHtml += `</ul></div>`;
      }
      totalUploaded += data.success_count; totalRows += data.total_rows; totalEmpty += data.empty_rows;
    } catch (err) {
      fileHtml += `<span class="text-red-600">Ошибка загрузки: ${err}</span>`; errorFiles += 1;
    }
    fileHtml += `</div>`; overallHtml += fileHtml;
  }
  overallHtml = `<div class="mb-4 p-2 rounded bg-blue-50 border border-blue-200">
      <b>Всего файлов:</b> ${fileList.length} &nbsp;|&nbsp;
      <b>Импортировано строк:</b> ${totalUploaded} / ${totalRows}
      ${totalEmpty ? `&nbsp;|&nbsp;<b>Пустых строк:</b> ${totalEmpty}` : ""}
      ${errorFiles > 0 ? `<br><span class="text-red-600">Файлов с ошибками: ${errorFiles}</span>` : ""}
    </div>` + overallHtml;
  statusDiv.innerHTML = overallHtml;
}

// ================== RANGE SLIDER (РЕЙТИНГ) ==================
function setSliderTrack() {
  const percent1 = ((parseInt(minRange.value) - sliderMin) / (sliderMax - sliderMin)) * 100;
  const percent2 = ((parseInt(maxRange.value) - sliderMin) / (sliderMax - sliderMin)) * 100;
  sliderTrack.style.left = percent1 + "%";
  sliderTrack.style.width = (percent2 - percent1) + "%";
}
function updateSliderValues() {
  let minVal = parseInt(minRange.value), maxVal = parseInt(maxRange.value);
  if (maxVal - minVal <= minGap) {
    if (event.target === minRange) {
      minVal = maxVal - minGap; minRange.value = minVal;
    } else {
      maxVal = minVal + minGap; maxRange.value = maxVal;
    }
  }
  minValue.textContent = parseInt(minRange.value);
  maxValue.textContent = parseInt(maxRange.value);
  setSliderTrack();
}
minRange.addEventListener('input', updateSliderValues);
maxRange.addEventListener('input', updateSliderValues);
setSliderTrack(); updateSliderValues();
clickArea.addEventListener('mousedown', function(e) {
  const rect = sliderRoot.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const percent = clickX / rect.width;
  const value = percent * (sliderMax - sliderMin) + sliderMin;
  const distToMin = Math.abs(value - parseInt(minRange.value));
  const distToMax = Math.abs(value - parseInt(maxRange.value));
  if (distToMin < distToMax) {
    let newVal = Math.min(value, parseInt(maxRange.value) - minGap);
    minRange.value = newVal.toFixed(1);
    minRange.dispatchEvent(new Event('input'));
  } else {
    let newVal = Math.max(value, parseInt(minRange.value) + minGap);
    maxRange.value = newVal.toFixed(1);
    maxRange.dispatchEvent(new Event('input'));
  }
});
// — Range-slider фильтрация —
minRange.addEventListener('change', () => { currentPage = 1; fetchPage(); });
maxRange.addEventListener('change', () => { currentPage = 1; fetchPage(); });

// При загрузке страницы - название кнопки по умолчанию
rangeSliderBtn.textContent = 'Применить фильтр';

// --- Применение/отмена фильтра ---
rangeSliderBtn.addEventListener('click', function(e) {
  e.preventDefault();

  if (!ratingFilterActive) {
    // --- Применяем фильтр по выбранному диапазону ---
    // (Тут ты уже вызываешь fetchPage() с учетом слайдера, как сейчас)
    //currentPage = 1;
    fetchPage();
    rangeSliderBtn.textContent = 'Отменить фильтр';
    ratingFilterActive = true;
  } else {
    // --- Сброс только фильтра по рейтингу ---
    minRange.value = sliderMin;
    maxRange.value = sliderMax;
    minValue.textContent = sliderMin;
    maxValue.textContent = sliderMax;
    setSliderTrack();
    fetchPage(); // заново применить фильтр (отобразятся все отзывы)
    rangeSliderBtn.textContent = 'Применить фильтр';
    ratingFilterActive = false;
  }
});

// ================== FILTERS + TABLE + PAGINATION ==================
// Собирает параметры фильтрации, сортировки и пагинации
function getReviewFilters() {
  const productId = analyzeButton.dataset.productId;
  const params = new URLSearchParams({
    product_id: productId,
    page: currentPage,
    limit: pageLimitSelect.value,
    sort_by: sortBy,
    sort_dir: sortDir,
    normalized_rating_min: minRange.value,
    normalized_rating_max: maxRange.value
  });
  if (filterInputs[0].value) params.append('importance', filterInputs[0].value);
  if (filterInputs[1].value) params.append('source', filterInputs[1].value);
  if (filterInputs[2].value) params.append('text', filterInputs[2].value);
  if (filterInputs[3].value) params.append('advantages', filterInputs[3].value);
  if (filterInputs[4].value) params.append('disadvantages', filterInputs[4].value);
  return params.toString();
}
// --- Фильтрация по Enter или change ---
filterInputs.forEach(input => {
  if (input.tagName === "INPUT") {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') { currentPage = 1; fetchPage(); }
    });
  } else {
    input.addEventListener('change', function() { currentPage = 1; fetchPage(); });
  }
});

// --- Сброс фильтров ---
toggleFilterBtn.addEventListener('click', function(e) {
  e.preventDefault();
  const isHidden = filterRow.classList.contains('hidden');
  if (isHidden) {
    filterRow.classList.remove('hidden');
    this.textContent = 'Выкл. отбор';
    filterHint.style.display = 'inline';
    filterRow.querySelector('input')?.focus();
  } else {
    filterRow.classList.add('hidden');
    this.textContent = 'Вкл. отбор';
    filterHint.style.display = 'none';
    filterInputs.forEach(inp => { if (inp.tagName === 'SELECT') inp.selectedIndex = 0; else inp.value = '' });
    minRange.value = sliderMin;
    maxRange.value = sliderMax;
    updateSliderValues();
    currentPage = 1;
    fetchPage();
  }
});
pageLimitSelect?.addEventListener('change', function() { currentPage = 1; fetchPage(); });

// --- Сортировка ---
document.querySelectorAll('th a[data-sort]').forEach(link => {
  link.addEventListener('click', function(e) {
    e.preventDefault();
    const newSort = this.getAttribute('data-sort');
    if (sortBy === newSort) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    else { sortBy = newSort; sortDir = 'asc'; }
    currentPage = 1; fetchPage();
  });
});
resetSortBtn?.addEventListener('click', function() {
  sortBy = 'id'; sortDir = 'asc'; currentPage = 1; fetchPage();
});

// ================== TABLE RENDER + PAGINATION ==================
function fetchPage(highlightId = null) {
  fetch('/analyze/data?' + getReviewFilters())
    .then(response => response.json())
    .then(data => {
      if (data.page > data.total_pages && data.total_pages > 0) {
        currentPage = data.total_pages;
        fetchPage(highlightId); return;
      }
      updateReviewsTable(data, highlightId);
      renderPagination(data.limit, data.page, data.total, data.total_pages);
    });
}

function updateReviewsTable(reviews, highlightId) {
  tableReviewsTBody.innerHTML = '';
  if (!reviews || !Array.isArray(reviews.items)) reviews = {items: []};
  if (!reviews.items || !reviews.items.length) {
    tableReviewsTBody.innerHTML = `<tr><td colspan="7" class="text-center text-gray-400">Нет отзывов</td></tr>`;
    return;
  }
  reviews.items.forEach(review => {
    const highlightClass = (highlightId && review.id == highlightId) ? 'bg-yellow-100' : '';
    tableReviewsTBody.innerHTML += `
      <tr 
        id="review-row-${review.id}"
        data-raw_rating="${ review.raw_rating }"
        data-rating="${ review.rating }"
        data-max_rating="${ review.max_rating }"
        data-normalized_rating="${ review.normalized_rating }"
        class="${highlightClass}"
      >
        <td class="border px-2 py-1" data-field="importance">${review.importance || ''}</td>
        <td class="border px-2 py-1" data-field="source">${review.source || ''}</td>
        <td class="border px-2 py-1" data-field="text">${review.text || ''}</td>
        <td class="border px-2 py-1" data-field="advantages">${review.advantages || ''}</td>
        <td class="border px-2 py-1" data-field="disadvantages">${review.disadvantages || ''}</td>
        <td class="border px-2 py-1">
          <div class="flex flex-col items-start">
            <span>${review.raw_rating ? review.raw_rating : `${review.rating ?? 0}/${review.max_rating ?? 0}`}</span>
            <span class="flex items-center text-xs text-blue-600 font-semibold mt-0.5">
              <svg class="w-4 h-4 mr-1 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.122-6.545L.488 6.91l6.561-.955L10 0l2.951 5.955 6.561.955-4.756 4.635 1.122 6.545z"/></svg>
              ${ review.normalized_rating  ?? 0}%
            </span>
          </div>
        </td>
        <td>
          <button class="btn edit-review-btn" data-id="${ review.id }" data-product-id="${ review.product_id }" type="button">Редактировать</button>
          <button class="btn btn-sm btn-warning bg-gray-300 text-white p-1 rounded hover:bg-gray-500 mr-2 delete-btn" data-id="${review.id}">Удалить</button>
        </td>
      </tr>
    `;
  });
}




// ================== MODAL ==================
const reviewModal = document.getElementById('review-modal');
const reviewForm = document.getElementById('review-form');
const addBtn = document.getElementById('add-review-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const reviewError = document.getElementById('review-error');
const modalTitle = document.getElementById('modal-title');

// Открыть модалку для ДОБАВЛЕНИЯ
addBtn.addEventListener('click', () => {
  modalTitle.textContent = "Добавить отзыв";
  reviewForm.reset();
  reviewForm.review_id.value = ""; // нет id для нового
  reviewModal.classList.remove('hidden');
  reviewError.textContent = "";
});

// Открыть модалку для РЕДАКТИРОВАНИЯ (делегирование клика по "Редактировать" рядом с отзывом)
document.getElementById('reviews-tbody').addEventListener('click', function(e) {
  const btn = e.target.closest('.edit-review-btn');
  if (!btn) return;

  // Здесь получаешь данные отзыва из data-атрибутов или из строки таблицы (лучше из таблицы/JS)
  const row = btn.closest('tr');
  reviewForm.review_id.value = btn.dataset.id;
  reviewForm.product_id.value = btn.dataset.productId;
  reviewForm.importance.value = row.querySelector('[data-field="importance"]').textContent;
  reviewForm.source.value = row.querySelector('[data-field="source"]').textContent;
  reviewForm.text.value = row.querySelector('[data-field="text"]').textContent;
  reviewForm.advantages.value = row.querySelector('[data-field="advantages"]').textContent;
  reviewForm.disadvantages.value = row.querySelector('[data-field="disadvantages"]').textContent;
  reviewForm.raw_rating.value = row.dataset.raw_rating || '';
  reviewForm.rating.value = row.dataset.rating || 0;
  reviewForm.max_rating.value = row.dataset.max_rating || 0;
  reviewForm.normalized_rating.value = row.dataset.normalized_rating || 0;

  modalTitle.textContent = "Редактировать отзыв";
  reviewModal.classList.remove('hidden');
  reviewError.textContent = "";
});


reviewForm.addEventListener('keydown', function(e) {
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault();
    reviewForm.requestSubmit(); // Отправить форму
  }
});

// Обработка Enter для blur
function handleInputEnterBlur(input) {
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();        // Не отправлять форму!
      input.blur();              // Снять фокус = применить
    }
  });
}

// Для всех важных input
handleInputEnterBlur(document.getElementById('importance'));
handleInputEnterBlur(document.getElementById('raw_rating'));
handleInputEnterBlur(document.getElementById('rating'));
handleInputEnterBlur(document.getElementById('max_rating'));

// Закрыть модалку
closeModalBtn.addEventListener('click', () => {
  reviewModal.classList.add('hidden');
  reviewError.textContent = "";
});

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

  ratingInput.addEventListener('blur', updateNormalized);
  maxRatingInput.addEventListener('blur', updateNormalized);

  // При загрузке формы также считаем
  updateNormalized();
});

// Отправка формы (создание или редактирование — решается по наличию review_id)
reviewForm.addEventListener('submit', async function(e) {
  e.preventDefault();
  const reviewId = reviewForm.review_id.value;
  const product_id = reviewForm.product_id.value;
  const url = reviewId ? `/review/${reviewId}/update` : `/review/${product_id}/add`;
  const method = reviewId ? "PUT" : "POST";
  const data = {
    importance: this.importance.value,
    source: this.source.value,
    text: this.text.value,
    advantages: this.advantages.value,
    disadvantages: this.disadvantages.value,
    raw_rating: this.raw_rating.value,
    rating: this.rating.value,
    max_rating: this.max_rating.value,
    normalized_rating: this.normalized_rating.value
  };
  console.log("data", data);
  try {
    const resp = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCSRFToken(),
      },
      credentials: 'same-origin',
      body: JSON.stringify(data),
    });
    const result = await resp.json();
    if (resp.ok) {
      reviewModal.classList.add('hidden');

      // --- Новый отзыв
      if (!reviewId) {
        // Сначала получи totalPages, потом на последнюю страницу и выделить строку
        fetch('/analyze/data?' + getReviewFilters().replace(/page=\d+/, 'page=1'))
          .then(response => response.json())
          .then(reviewsData => {
            const totalPages = reviewsData.total_pages;
            currentPage = totalPages;
            fetchPage(result.id); // выделить новую строку
          });
      } else {
        // --- Редактирование: остаёмся на месте, просто обновляем таблицу и выделяем строку
        fetchPage(reviewId); // выделить отредактированную строку
      }
    } else {
      reviewError.textContent = result.detail || "Ошибка сохранения";
    }
  } catch (err) {
    reviewError.textContent = err.message;
  }
});



// ================== ANALIZE ==================
//Запустить анализ отзывов (отправка на сервер)
function toNumberOrNull(val) {
  return val === "" || val === undefined || val === null ? null : Number(val);
}

async function analyzeProduct() {
  try {
    setStatus("Анализируем отзывы...", "blue");
    analyzeButton.disabled = true;

    const productId = analyzeButton.dataset.productId;
    const promtId = document.getElementById("promt_id").value;
    const params = new URLSearchParams(getReviewFilters());
    const filters = Object.fromEntries(params.entries());

    filters.promt_id = promtId; // если промт тоже фильтр

    Object.keys(filters).forEach(key => {
      // Преобразуем к числу если это числовое поле фильтра
      if (["promt_id", "importance", "normalized_rating_min", "normalized_rating_max"].includes(key)) {
        if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
          filters[key] = Number(filters[key]);
        }
      }
      // Теперь убираем всё, что не выбрано:
      // (0 и пустая строка — если не выбран фильтр)
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

    // 3. Делаем POST-запрос на backend, передавая JSON
    const response = await fetch(`/analyze/${productId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRF-Token": getCSRFToken()
      },
      credentials: "same-origin",
      body: JSON.stringify(payload)
    });

    // 4. Читаем ответ сервера
    const data = await response.json();
    
    // 5. Проверяем результат
    if (!response.ok) {
        console.error("Ошибка FastAPI:", data.detail);
        throw new Error(data.detail || "Ошибка на сервере");
    }

    setStatus("Анализ завершён успешно!", "green");
    document.getElementById('analysis_result').value = data.result;
  } catch (error) {
    setStatus("Ошибка анализа: " + error.message, "red");
  } finally {
    analyzeButton.disabled = false;
  }
}

// Установить текстовый статус
function setStatus(message, color) {
  analyzeStatus.textContent = message;
  analyzeStatus.style.color = color;
}

analyzeButton.addEventListener('click', analyzeProduct);



// ================== MODAL ==================
tableReviewsTBody.addEventListener('click', function(e) {
  const tr = e.target.closest('tr');
  if (!tr) return;
  // Снимаем выделение со всех
  tableReviewsTBody.querySelectorAll('tr').forEach(row => row.classList.remove('bg-yellow-100'));
  // Выделяем текущий
  tr.classList.add('bg-yellow-100');
});


document.addEventListener("DOMContentLoaded", function () {
  // Лучше делегировать на общий контейнер
  document.getElementById('reviews-tbody').addEventListener('click', async function (e) {
    const btn = e.target.closest('.delete-btn');
    if (!btn) return;
    const reviewId = btn.getAttribute('data-id');
    if (!confirm("Удалить этот отзыв?")) return;

    try {
      const resp = await fetch(`/review/${reviewId}/delete`, {
        method: "DELETE",
        headers: {
          "Accept": "application/json",
          "X-CSRF-Token": getCSRFToken()
        },
        credentials: "same-origin",
      });
      const data = await resp.json();
      if (data.success) {
        // После удаления — нужно узнать, остались ли записи на этой странице:
        fetch('/analyze/data?' + getReviewFilters())
          .then(response => response.json())
          .then(data => {
            // Если текущая страница пустая, перейти на предыдущую
            if (data.items.length === 0 && currentPage > 1) {
              currentPage--;
              fetchPage();
            } else {
              fetchPage();
            }
          });
      } else {
        alert(data.error || "Ошибка при удалении");
      }
    } catch (e) {
      alert("Сетевая ошибка!");
    }
  });
});








document.getElementById('clear-reviews-btn').addEventListener('click', async function() {
  if (!confirm("Вы уверены, что хотите удалить все отзывы по этому товару?")) return;

  const productId = document.getElementById('clear-reviews-btn').dataset.productId;
  try {
    const response = await fetch(`/analyze/${productId}/reviews/clear`, {
      method: "DELETE",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRF-Token": getCSRFToken()
      },
      credentials: "same-origin",
    });
    const data = await response.json();
    if (data.status === "ok") {
      alert(`Удалено отзывов: ${data.deleted}`);
      fetchPage();
    } else {
      alert("Ошибка при удалении отзывов");
    }
  } catch (err) {
    alert("Ошибка сети или сервера: " + err.message);
  }
});








// ================== Инициализация ==================
window.addEventListener('DOMContentLoaded', fetchPage);
