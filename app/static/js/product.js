document.addEventListener("DOMContentLoaded", function() {
  // 1. Открытие диалога выбора файла по клику на wrapper
  const imageWrapper = document.getElementById('main_image_wrapper');
  const imageInput = document.getElementById('main_image_input');
  const previewImage = document.getElementById('main_image_preview');

  if (imageWrapper && imageInput) {
    imageWrapper.addEventListener('click', function() {
      imageInput.click();
    });
  }

  // 2. Превью выбранного изображения
  if (imageInput && previewImage) {
    imageInput.addEventListener('change', () => {
      const file = imageInput.files[0];
      if (file) {
        const objectUrl = URL.createObjectURL(file);
        previewImage.src = objectUrl;
      }
    });
  }

  // 3. Сохранение данных на сервере при нажатии на кнопку "Сохранить"
  const form = document.getElementById('product-form');
  if (!form) return;

  form.addEventListener('submit', async function(event) {
    event.preventDefault();

    // Собираем FormData с формы
    const formData = new FormData(form);

    const saveUrl = form.getAttribute('data-save-url');

    try {
      const response = await fetch(saveUrl, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
          "X-CSRF-Token": getCSRFToken()
        }
      });

      // Проверяем, что ответ именно JSON
      let data;
      try {
        data = await response.json();
      } catch (e) {
        alert("Ошибка: сервер вернул не JSON");
        return;
      }

      if (response.ok && data.url) {
        window.location.href = data.url;
      } else {
        alert(data.detail || 'Ошибка при сохранении');
      }

    } catch (error) {
      console.error("Error:", error);
      alert('Ошибка при отправке данных');
    }
  });
});
