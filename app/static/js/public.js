document.addEventListener('DOMContentLoaded', function() {

  const slider = document.getElementById('testimonialsSlider');
  const slides = Array.from(slider.children);
  const prevBtn = document.getElementById('sliderPrev');
  const nextBtn = document.getElementById('sliderNext');

  let slidesToShow = 3;
  let currentIndex = 0;

  function getSlidesToShow() {
    if (window.innerWidth < 768) return 1; // mobile
    if (window.innerWidth < 1024) return 2; // tablet
    return 3; // desktop
  }

  function updateSlider() {
    slidesToShow = getSlidesToShow();

    // Ограничить currentIndex, чтобы не было пустых слайдов справа
    if (currentIndex > slides.length - slidesToShow) {
      currentIndex = Math.max(0, slides.length - slidesToShow);
    }

    slides.forEach((slide, i) => {
      if (i >= currentIndex && i < currentIndex + slidesToShow) {
        slide.classList.remove('hidden');
      } else {
        slide.classList.add('hidden');
      }
    });

    // Деактивировать стрелки на концах
    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex >= slides.length - slidesToShow;
    prevBtn.classList.toggle('opacity-50', prevBtn.disabled);
    nextBtn.classList.toggle('opacity-50', nextBtn.disabled);
  }

  function scrollPrev() {
    slidesToShow = getSlidesToShow();
    currentIndex = Math.max(0, currentIndex - slidesToShow);
    updateSlider();
  }

  function scrollNext() {
    slidesToShow = getSlidesToShow();
    currentIndex = Math.min(slides.length - slidesToShow, currentIndex + slidesToShow);
    updateSlider();
  }

  prevBtn.addEventListener('click', scrollPrev);
  nextBtn.addEventListener('click', scrollNext);
  window.addEventListener('resize', updateSlider);

  // Инициализация
  updateSlider();

  // Мобильное меню
  const burgerBtn = document.getElementById('burgerBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  const closeMenuBtn = document.getElementById('closeMenu');

  // Открытие меню
  burgerBtn.addEventListener('click', () => {
    mobileMenu.classList.remove('hidden');
  });

  // Закрытие по крестику
  closeMenuBtn.addEventListener('click', () => {
    mobileMenu.classList.add('hidden');
  });

  // Закрытие по клику на любой пункт меню или кнопку
  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      mobileMenu.classList.add('hidden');
    });
  });

  // Управление анимациями знаков вопроса
  const questionMarks = document.querySelectorAll('[class*="question-mark"]');
  
  // Функция для случайного изменения задержки анимации
  function randomizeAnimationDelays() {
    questionMarks.forEach((mark, index) => {
      const randomDelay = Math.random() * 3; // случайная задержка от 0 до 3 секунд
      mark.style.setProperty('--fade-delay', `${randomDelay}s`);
    });
  }

  // Функция для паузы/возобновления анимаций при скролле
  function handleScrollAnimations() {
    const sections = [
      { selector: '.firstscreen__content', name: 'hero' },
      { selector: '.analyze', name: 'analyze' },
      { selector: '.faq', name: 'faq' },
      { selector: '.finalcta', name: 'finalcta' }
    ];

    sections.forEach(section => {
      const element = document.querySelector(section.selector);
      if (!element) return;

      const rect = element.getBoundingClientRect();
      const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
      
      // Находим все анимированные элементы в этой секции
      const sectionQuestionMarks = element.querySelectorAll('[class*="question-mark"]');
      
      sectionQuestionMarks.forEach(mark => {
        if (isVisible) {
          // Возобновляем анимацию
          mark.style.animationPlayState = 'running';
          // Принудительно перезапускаем анимацию для надежности
          const animationName = mark.style.animationName || 
            getComputedStyle(mark).animationName;
          if (animationName && animationName !== 'none') {
            mark.style.animation = 'none';
            mark.offsetHeight; // Принудительный reflow
            mark.style.animation = '';
          }
        } else {
          mark.style.animationPlayState = 'paused';
        }
      });
    });
  }

  // Инициализация анимаций
  randomizeAnimationDelays();
  
  // Обновление задержек каждые 30 секунд для разнообразия
  setInterval(randomizeAnimationDelays, 30000);
  
  // Используем Intersection Observer для более точного контроля анимаций
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1 // Анимация запускается когда 10% элемента видно
  };

  const animationObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const questionMarks = entry.target.querySelectorAll('[class*="question-mark"]');
      
      questionMarks.forEach(mark => {
        if (entry.isIntersecting) {
          // Элемент виден - запускаем анимацию
          mark.style.animationPlayState = 'running';
          mark.style.opacity = '1';
        } else {
          // Элемент не виден - останавливаем анимацию
          mark.style.animationPlayState = 'paused';
        }
      });
    });
  }, observerOptions);

  // Наблюдаем за всеми секциями с анимациями
  const animatedSections = document.querySelectorAll('.firstscreen__content, .analyze, .faq, .finalcta');
  animatedSections.forEach(section => {
    animationObserver.observe(section);
  });

  // Обработка скролла (резервный метод)
  window.addEventListener('scroll', handleScrollAnimations);
  
  // Обработка изменения размера окна
  window.addEventListener('resize', () => {
    setTimeout(randomizeAnimationDelays, 100);
  });

  // Динамический счетчик ограниченности
  function updateLimitedSpots() {
    const counterElement = document.querySelector('.finalcta__counter span');
    if (!counterElement) return;

    // Генерируем случайное число от 60 до 85 для реалистичности
    const minSpots = 60;
    const maxSpots = 85;
    const currentSpots = Math.floor(Math.random() * (maxSpots - minSpots + 1)) + minSpots;
    
    counterElement.textContent = currentSpots;
  }

  // Обновляем счетчик при загрузке и каждые 30 секунд
  updateLimitedSpots();
  setInterval(updateLimitedSpots, 30000);

  // Анимация появления бейджа
  function animateBadge() {
    const badge = document.querySelector('.finalcta__badge');
    if (!badge) return;

    // Добавляем класс анимации
    badge.style.opacity = '0';
    badge.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
      badge.style.transition = 'all 0.6s ease-out';
      badge.style.opacity = '1';
      badge.style.transform = 'translateY(0)';
    }, 500);
  }

  // Запускаем анимацию бейджа
  setTimeout(animateBadge, 1000);

  // Функция для принудительного перезапуска всех анимаций
  function restartAllAnimations() {
    const allQuestionMarks = document.querySelectorAll('[class*="question-mark"]');
    allQuestionMarks.forEach(mark => {
      // Временно останавливаем анимацию
      mark.style.animationPlayState = 'paused';
      // Принудительно перезапускаем
      const computedStyle = getComputedStyle(mark);
      const animationName = computedStyle.animationName;
      if (animationName && animationName !== 'none') {
        mark.style.animation = 'none';
        mark.offsetHeight; // Принудительный reflow
        mark.style.animation = '';
        mark.style.animationPlayState = 'running';
      }
    });
  }

  // Перезапускаем анимации каждые 2 минуты для надежности
  setInterval(restartAllAnimations, 120000);
}); 

  