// Обработчик превью основного изображения
const input_image = document.getElementById('main_image_input');
const preview_image = document.getElementById('main_image_preview');
if (input_image && preview_image) {
  input_image.addEventListener('change', () => {
    const file = input_image.files[0];
    if (file) {
      const objectUrl = URL.createObjectURL(file);
      preview_image.src = objectUrl;
    }
  });
}

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
