// Получить токен из куки
function getCSRFToken() {
    // простейший способ, есть готовые либы для парсинга cookie
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];
  }

// Проверка разрешенных типов файлов для загрузки отзывов
function isAllowedFile(file) {
    const allowedExtensions = ['json', 'csv', 'xlsx'];
    const fileName = file.name.toLowerCase();
    const extension = fileName.split('.').pop();
    
    // Проверяем расширение файла
    if (allowedExtensions.includes(extension)) {
        return true;
    }
    
    // Дополнительная проверка MIME-типов
    const allowedMimeTypes = [
        'application/json',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ];
    
    return allowedMimeTypes.includes(file.type);
}