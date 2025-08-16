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
}); 

  