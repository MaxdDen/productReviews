// Получить токен из куки
function getCSRFToken() {
    // простейший способ, есть готовые либы для парсинга cookie
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];
  }