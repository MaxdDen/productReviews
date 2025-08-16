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
                        'Content-Type': 'application/x-www-form-urlencoded',
                        "X-CSRF-Token": getCSRFToken()
                    },
                    credentials: 'same-origin',
                    body: new URLSearchParams({ username, password, next_url: form.next_url ? form.next_url.value : '' })
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
        const nextUrlInput = loginForm.querySelector('input[name="next_url"]');
        handleAuthForm(
            loginForm,
            '/login',
            '#login-error',
            data => data.next || (nextUrlInput ? nextUrlInput.value : '/dashboard')
        );
    }

    if (registerForm) {
        // For registration, we are still sending JSON, so we need a separate handler or modify handleAuthForm
        // For now, let's assume registration is meant to stay as JSON as per the backend LoginInput model for /register
        // If registration also needs to be form data, this will need adjustment.
        // However, the original issue was with login.
        registerForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const username = registerForm.username.value;
            const password = registerForm.password.value;
            try {
                const response = await fetch('/register', { // Hardcoded URL for register
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json', // Kept as JSON for register
                        "X-CSRF-Token": getCSRFToken()
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Ошибка');
                window.location.href = '/login'; // onSuccessRedirect for register
            } catch (e) {
                document.querySelector('#register-error').innerText = e.message;
            }
        });
    }
});
