document.addEventListener('DOMContentLoaded', async () => {
    const form = document.getElementById('identify-form');
    const uploadInput = document.getElementById('image-upload');
    const uploadZone = document.getElementById('upload-zone');
    const gallery = document.getElementById('gallery');
    const previewZone = document.getElementById('preview-zone');
    const resultFields = document.getElementById('result-fields');
    const storeList = document.getElementById('store-list');
    const resultStores = document.getElementById('result-stores');
    const confirmSection = document.getElementById('confirm-section');
    const checkAllBtn = document.getElementById('select-all');
    const uncheckAllBtn = document.getElementById('uncheck-all');
    const deleteSelectedBtn = document.getElementById('delete-selected');
    const selectedCount = document.getElementById('selected-count');
      
    // Скрытие системного поведения для всей страницы
    window.addEventListener('dragover', e => e.preventDefault());
    window.addEventListener('drop', e => e.preventDefault());

    // Блок для информации о "плохих" файлах
    const invalidList = document.createElement('div');
    invalidList.id = 'invalid-files-list';
    invalidList.className = 'mt-4 text-red-600';
    uploadZone.after(invalidList);

    // Отключаем дефолт по drag/drop по всей странице
    window.addEventListener('dragover', e => e.preventDefault());
    window.addEventListener('drop', e => e.preventDefault());

    // Подсветка зоны drag/drop
    ['dragenter', 'dragover'].forEach(evt =>
      uploadZone.addEventListener(evt, e => {
        e.preventDefault();
        uploadZone.classList.add('border-blue-600');
      })
    );
    ['dragleave', 'drop'].forEach(evt =>
      uploadZone.addEventListener(evt, e => {
        e.preventDefault();
        uploadZone.classList.remove('border-blue-600');
      })
    );

    // Обработка drop внутри зоны
    uploadZone.addEventListener('drop', e => {
      e.preventDefault();
      handleFiles(e.dataTransfer.files);
    });

    // Обработка выбора через диалог
    uploadInput.addEventListener('change', () => {
      handleFiles(uploadInput.files);
      uploadInput.value = '';
    });

    // Функция обработки файлов
    function handleFiles(files) {
      const validFiles = [];
      const invalidFiles = [];

      Array.from(files).forEach(file => {
        if (file.type.startsWith('image/')) {
          validFiles.push(file);
        } else {
          invalidFiles.push(file.name);
        }
      });

      validFiles.forEach(file => addFileToGallery(file));
      renderInvalidFiles(invalidFiles);
      updateCount();
    }

    // Рендеринг превью
    function addFileToGallery(file) {
      const reader = new FileReader();
      reader.onload = e => {
        const wrapper = document.createElement('div');
        wrapper.classList.add('relative', 'w-24', 'h-24', 'border');

        const img = document.createElement('img');
        img.src = e.target.result;
        img.classList.add('object-cover', 'w-full', 'h-full');

        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.checked = true;
        chk.classList.add('absolute', 'top-1', 'right-1', 'bg-white', 'rounded');

        wrapper.append(img, chk);
        wrapper.fileBlob = file;
        gallery.appendChild(wrapper);
        updateCount();
      };
      reader.readAsDataURL(file);
    }

    // Вывод списка невалидных файлов
    function renderInvalidFiles(list) {
      invalidList.innerHTML = '';
      if (!list.length) return;

      const title = document.createElement('p');
      title.textContent = 'Не добавлены (не изображения):';
      const ul = document.createElement('ul');
      list.forEach(name => {
        const li = document.createElement('li');
        li.textContent = name;
        ul.appendChild(li);
      });
      invalidList.append(title, ul);
    }

    // Пересчет выделенных файлов при смене каждого чекбокса
    gallery.addEventListener('change', e => {
      if (e.target.matches('input[type="checkbox"]')) updateCount();
    });

    // Установить флажки на всех изображениях
    function updateCount() {
      const count = gallery.querySelectorAll('input[type="checkbox"]:checked').length;
      selectedCount.textContent = `Выбрано: ${count}`;
    }

    // Установить флажки на всех изображениях
    checkAllBtn.addEventListener('click', () => {
      gallery.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
      updateCount();
    });

    // Снять флажки со всех изображений
    uncheckAllBtn.addEventListener('click', () => {
      gallery.querySelectorAll('input[type="checkbox"]')
        .forEach(cb => cb.checked = false);
      updateCount();
    });

    // Удалить отмеченные изображения из галереи
    deleteSelectedBtn.addEventListener('click', () => {
      const count = gallery.querySelectorAll('input[type="checkbox"]:checked').length;
      if (count === 0) return; // нет отмеченных — ничего не делаем
    
      if (!confirm(`Вы действительно хотите удалить ${count} элементов?`)) return;
    
      gallery.querySelectorAll('.relative').forEach(wrapper => {
        if (wrapper.querySelector('input[type="checkbox"]').checked) wrapper.remove();
      });
      updateCount();
    });

    // Удаление одного элемента по двойному клику (дополнительно)
    gallery.addEventListener('dblclick', e => {
      const wrapper = e.target.closest('div');
      if (!wrapper) return;
      if (confirm('Удалить это изображение?')) {
        wrapper.remove();
        updateCount();
      }
    });

    Sortable.create(gallery, {
      animation: 150,
      ghostClass: 'opacity-50',
      handle: 'img',
    });



    // 📷 Камера
    const cameraButton = document.getElementById('camera-capture');

    // Получаем deviceId один раз
    let deviceId = sessionStorage.getItem('device_id');
    if (!deviceId && window.FingerprintJS) {
      try {
        const fp = await FingerprintJS.load();
        const res = await fp.get();
        deviceId = res.visitorId;
        sessionStorage.setItem('device_id', deviceId);
      } catch(e) {
        console.error('FingerprintJS error', e);
      }
    }
    
    // Логика определения типа устройства
    function hasTouch() {
      return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    function isSmallScreen() {
      return window.matchMedia('(max-width: 800px)').matches;
    }
    function getDeviceType() {
      if (!hasTouch() && !isSmallScreen()) return 'desktop';
      if (hasTouch() && isSmallScreen()) return 'mobile';
      return 'ambiguous';
    }

    // Получить сохраненный режим камеры (modal или fullscreen)
    function loadCameraMode() {
      return sessionStorage.getItem('cameraMode');  // или localStorage
    }

    // Сохранить выбор пользователя
    function saveCameraMode(mode) {
      sessionStorage.setItem('cameraMode', mode);
    }

    // Обработчик кнопки “Сделать фото”
    cameraButton.addEventListener('click', async () => {
      const saved = loadCameraMode(); // либо null, либо 'modal'/'fullscreen'
      let mode;
    
      if (saved) {
        mode = saved;
      } else {
        const type = getDeviceType(); // 'desktop', 'mobile' или 'ambiguous'
        if (type === 'desktop') mode = 'modal';
        else if (type === 'mobile') mode = 'fullscreen';
        else {
          const userChoseModal = confirm("ОК — модал, Отмена — fullscreen");
          mode = userChoseModal ? 'modal' : 'fullscreen';
          saveCameraMode(mode);
        }
      }
    
      const deviceType = (mode === 'modal') ? 'desktop' : 'mobile';

      await fetch('/device/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: deviceId,
          device_type: deviceType
        })
      });
    
      if (deviceType === 'desktop') openCameraModal();
      else openMobileCamera();
    });

    async function openCameraModal() {
      const modal = document.getElementById('camera-modal');
      const video = document.getElementById('camera-video');
      const canvas = document.getElementById('camera-canvas');
      const takeBtn = document.getElementById('take-photo');
      const cancelBtn = document.getElementById('cancel-photo');
      const previewCheckbox = document.getElementById('preview-checkbox');

      modal.classList.remove('hidden');
      modal.setAttribute('tabindex', '0');
      modal.focus();
    
      if (!video.srcObject) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
          video.srcObject = stream;
          await video.play();
        } catch (err) {
          alert('Не удалось открыть камеру: ' + err.message);
          return closeModal();
        }
      }
    
      const escHandler = e => {
        if (e.key === 'Escape') closeModal();
        if (e.key === 'Enter' || e.key === ' ') takeSnapshot();
      };
      modal.addEventListener('keydown', escHandler);
    
      takeBtn.onclick = takeSnapshot;
      cancelBtn.onclick = closeModal;
      modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
    
      function closeModal() {
        modal.classList.add('hidden');
        const stream = video.srcObject;
        if (stream) stream.getTracks().forEach(t => t.stop());
        video.srcObject = null;
        modal.removeEventListener('keydown', escHandler);
      }
    
      // снимок + предпросмотр
      function takeSnapshot() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        canvas.toBlob(blob => {
          if (previewCheckbox.checked) {
            // показываем preview модал, после подтверждения добавляем
            showPreviewModal(blob);
          } else {
            // сразу добавляем в галерею
            addFileToGallery(new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' }));
          }
        }, 'image/jpeg');
      }
    }
    
    function showPreviewModal(blob) {
      const previewModal = document.getElementById('photo-preview-modal');
      const img = document.getElementById('photo-preview-img');
      const confirmBtn = document.getElementById('confirm-photo');
      const cancelBtn = document.getElementById('cancel-preview');
    
      img.src = URL.createObjectURL(blob);
      previewModal.classList.remove('hidden');
    
      const escHandler = e => { if (e.key === 'Escape') hidePreview(); };
      document.addEventListener('keydown', escHandler);
    
      confirmBtn.onclick = () => {
        addFileToGallery(new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' }));
        hidePreview();
      };
      cancelBtn.onclick = hidePreview;
    
      function hidePreview() {
        previewModal.classList.add('hidden');
        URL.revokeObjectURL(img.src);
        document.removeEventListener('keydown', escHandler);
      }
    }
        









  
    // 📡 Отправка формы
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
    
      // Добавляем выбранные по чекбоксу файлы
      Array.from(gallery.children).forEach((wrapper, i) => {
        if (wrapper.querySelector('input[type="checkbox"]').checked) {
          formData.append('images', wrapper.fileBlob, `image${i}.jpg`);
        }
      });
    
      const url = e.target.dataset.identifyUrl;
      const res = await fetch(url, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });
  
      if (!res.ok) {
        alert('Ошибка при определении товара');
        return;
      }
  
      const data = await res.json();
  
      // Заполняем поля
      resultFields.classList.remove('hidden');
      document.getElementById('result-ean').value = data.ean || '';
      document.getElementById('result-upc').value = data.upc || '';
      document.getElementById('result-serial').value = data.serial_number || '';
      document.getElementById('result-name').value = data.name || '';
      document.getElementById('result-barcode').value = data.barcode || '';
      document.getElementById('result-link').value = data.product_link || '';
  
      // Магазины
      storeList.innerHTML = '';
      if (data.stores && data.stores.length > 0) {
        resultStores.classList.remove('hidden');
        data.stores.forEach(store => {
          const li = document.createElement('li');
          const a = document.createElement('a');
          a.href = store.url;
          a.textContent = store.name;
          a.target = '_blank';
          li.appendChild(a);
          storeList.appendChild(li);
        });
      }
  
      // Кнопка подтверждения
      confirmSection.classList.remove('hidden');

    });



    const saveBtn = document.getElementById('save-product');
    const formPersist = document.getElementById('product-persist-form'); // id формы определения товара
  
    saveBtn.addEventListener('click', async () => {
      const formData = new FormData();
  
      // Имя товара
      let name = document.getElementById('result-name').value;
      if (!name) {
        const now = new Date();
        const formatted = now.toISOString().slice(0,16).replace('T', ' ');
        name = `Товар ${formatted}`;
      }
      formData.append('name', name);
  
      // Фото
      /*const wrappers = Array.from(document.getElementById('gallery').children);
      const checkedWrappers = wrappers.filter(w => w.querySelector('input[type="checkbox"]').checked);
      if (checkedWrappers.length > 0) {
        const blob = checkedWrappers[0].fileBlob;
        formData.append('main_image', blob, `photo.jpg`);
      }*/
      Array.from(gallery.children).forEach((wrapper, i) => {
        if (wrapper.querySelector('input[type="checkbox"]').checked) {
          formData.append('images', wrapper.fileBlob, `image${i}.jpg`);
        }
      });
      // (Опционально другие поля — EAN, UPC и т. д.)
      // formData.append('ean', document.getElementById('result-ean').value || '');
      // formData.append('upc', ...);
  
      console.log("name ", name)
      console.log("formData ", formData)
      try {
        const res = await fetch('/product/save', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRF-Token': getCSRFToken() },
          body: formData,
        });
  
        const data = await res.json();
  
        if (res.ok && data.url) {
          window.location.href = data.url;
        } else {
          alert(data.detail || data.error || 'Ошибка сервера при сохранении');
        }
      } catch (err) {
        console.error(err);
        alert('Сетевая ошибка при сохранении');
      }
    });

    let isDirty = false;

    function markDirty() { isDirty = true; }
    
    uploadInput.addEventListener('change', markDirty);
    gallery.addEventListener('click', markDirty);
    saveBtn.addEventListener('click', () => isDirty = false);
    
    window.addEventListener('beforeunload', e => {
      if (!isDirty) return;
      e.preventDefault();
      e.returnValue = '';
    });

  });

