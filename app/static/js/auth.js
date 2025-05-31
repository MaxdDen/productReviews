// auth.js
document.addEventListener("DOMContentLoaded", function() {
    // Универсально ищем форму по id
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    // Одна функция отправки
    async function handleAuthForm(form, url, errorSelector, onSuccessRedirect) {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            const username = form.username.value;
            const password = form.password.value;
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        "X-CSRF-Token": getCSRFToken()
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Ошибка');
                window.location.href = onSuccessRedirect(data);
            } catch (e) {
                document.querySelector(errorSelector).innerText = e.message;
            }
        });
    }

    if (loginForm) {
        handleAuthForm(
            loginForm,
            '/login',
            '#login-error',
            data => data.next || '/dashboard'
        );
    }

    if (registerForm) {
        handleAuthForm(
            registerForm,
            '/register',
            '#register-error',
            () => '/login'    // После регистрации всегда на /login
        );
    }
});
