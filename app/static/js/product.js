// Обработчик превью основного изображения
const inputImage = document.getElementById('main_image_input');
const previewImages = document.querySelectorAll('.main_image_preview');
const dropZones = document.querySelectorAll('.main_image_preview');
if (inputImage && previewImages.length) {
  inputImage.addEventListener('change', () => {
    const file = inputImage.files[0];
    if (file) handleImageFile(file);
  });
  // Клик по любому превью вызывает выбор файла
  previewImages.forEach(img => img.addEventListener('click', () => inputImage.click()));
}

function handleImageFile(file) {
  const maxSize = 5 * 1024 * 1024;
  if (!file.type.startsWith('image/')) {
    alert('Можно загружать только изображения');
    inputImage.value = '';
    return;
  }
  if (file.size > maxSize) {
    alert('Размер изображения не должен превышать 5 МБ');
    inputImage.value = '';
    return;
  }
  const objectUrl = URL.createObjectURL(file);
  previewImages.forEach(img => {
    img.src = objectUrl;
    img.onload = () => URL.revokeObjectURL(objectUrl);
  });
}

// Drag-and-drop поддержка
previewImages.forEach(img => {
  const zone = img.parentElement;
  if (!zone) return;
  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('ring-2', 'ring-[#A3B8F8]');
  });
  zone.addEventListener('dragleave', e => {
    e.preventDefault();
    zone.classList.remove('ring-2', 'ring-[#A3B8F8]');
  });
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('ring-2', 'ring-[#A3B8F8]');
    if (!e.dataTransfer || !e.dataTransfer.files || e.dataTransfer.files.length === 0) return;
    if (e.dataTransfer.files.length > 1) {
      alert('Можно загрузить только один файл за раз');
      return;
    }
    const file = e.dataTransfer.files[0];
    inputImage.files = e.dataTransfer.files; // для отправки формы
    handleImageFile(file);
  });
});

// Сохранение данных на сервере при нажатии на кнопку "Сохранить"
document.addEventListener("DOMContentLoaded", function() {
  const form = document.getElementById('product-form');
  if (!form) return;

  form.addEventListener('submit', async function(event) {
    event.preventDefault();

    // Собираем FormData с формы
    const formData = new FormData(form);

    // Получаем URL для сохранения (например: /product/save)
    const saveUrl = form.dataset.saveUrl;

    try {
      const response = await fetch(saveUrl, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          "X-CSRF-Token": getCSRFToken()
        }
      });

      const data = await response.json();
      if (response.ok && data.url) {
        window.location.href = data.url;
      } else {
        // Покажи ошибку от сервера
        const data = await response.json();
        alert(data.detail || 'Ошибка при сохранении');
      }

    } catch (error) {
      console.error("Error:", error);
      alert('Ошибка при отправке данных');
    }
  });
});
