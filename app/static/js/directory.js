document.addEventListener("DOMContentLoaded", function () {
  // --- Открытие модалки ---
  const modal = document.getElementById('directory-modal');
  const form = document.getElementById('directory-modal-form');
  const modalTitle = document.getElementById('modal-title');
  const modalName = document.getElementById('modal-name');
  const modalDesc = document.getElementById('modal-description');
  const modalId = document.getElementById('modal-item-id');
  const modalError = document.getElementById('modal-error');
  const closeModalBtn = document.getElementById('close-modal');
  const openCreateBtn = document.getElementById('open-create-modal');

  // Открытие на создание
  openCreateBtn.addEventListener('click', function() {
    modalTitle.innerText = "Добавить новый элемент";
    modalName.value = "";
    modalDesc.value = "";
    modalId.value = "";
    modalError.innerText = "";
    modal.classList.remove('hidden');
  });

  // Открытие на редактирование (делегирование)
  document.querySelectorAll('.edit-item-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const id = btn.dataset.id;
      const name = btn.dataset.name;
      const desc = btn.dataset.description;
      modalTitle.innerText = "Редактировать элемент";
      modalName.value = name || "";
      modalDesc.value = desc || "";
      modalId.value = id || "";
      modalError.innerText = "";
      modal.classList.remove('hidden');
    });
  });

  // Закрытие
  closeModalBtn.addEventListener('click', function() {
    modal.classList.add('hidden');
  });

  // --- Submit модалки ---
  form.addEventListener('submit', async function(event) {
    event.preventDefault();
    modalError.innerText = "";
    const itemId = modalId.value;
    const name = modalName.value.trim();
    const description = modalDesc.value.trim();
    const csrf_token = getCSRFToken();
    if (!csrf_token) {
      modalError.innerText = 'Нет CSRF токена!';
      return;
    }
    const directoryName = document.getElementById('open-create-modal').dataset.directoryName;

    let url, method;
    if (itemId) {
      // Редактирование
      url = `/directory/${directoryName}/update/${itemId}`;
      method = "POST";
    } else {
      // Создание
      url = `/directory/${directoryName}/new`;
      method = "POST";
    }
    try {
      const resp = await fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrf_token
        },
        credentials: "same-origin",
        body: JSON.stringify({ name, description })
      });
      if (resp.redirected) {
        window.location.href = resp.url;
        return;
      }
      const data = await resp.json();
      if (data.success) {
        window.location.reload();
      } else {
        modalError.innerText = data.error || "Ошибка при сохранении";
      }
    } catch (e) {
      modalError.innerText = "Сетевая ошибка!";
    }
  });
});

  // Удаление элемента
  document.querySelectorAll('.delete-item-btn').forEach(btn => {
    btn.addEventListener('click', async function () {
      const itemId = btn.getAttribute('data-id');
      const directoryName = btn.getAttribute('data-directory');
      if (!confirm("Удалить этот элемент?")) return;
      try {
        const resp = await fetch(`/directory/${directoryName}/delete/${itemId}`, {
          method: "DELETE",
          headers: {
            "Accept": "application/json",
            "X-CSRF-Token": getCSRFToken()
          }
        });
        const data = await resp.json();
        if (data.success) {
          // Можно сделать window.location.reload(), либо удалить строку из таблицы
          window.location.href = data.url;
        } else {
          alert(data.error || "Ошибка при удалении");
        }
      } catch (e) {
        alert("Сетевая ошибка!");
      }
    });
  });
