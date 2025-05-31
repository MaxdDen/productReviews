document.addEventListener('DOMContentLoaded', () => {
    const menuButton = document.getElementById('burger-button');
    const menu = document.getElementById('mobile-menu');
    const closeButton = document.getElementById('close-button');
  
    if (menuButton && closeButton && menu) {
      menuButton.addEventListener('click', () => {
        menu.classList.remove('hidden');
      });
  
      closeButton.addEventListener('click', () => {
        menu.classList.add('hidden');
      });
  
      document.addEventListener('click', (e) => {
        if (!menu.contains(e.target) && !menuButton.contains(e.target)) {
          menu.classList.add('hidden');
        }
      });
    }
  });


  