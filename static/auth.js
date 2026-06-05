const Auth = {
    async login(email, password) {
        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            return response.ok && data.success;
        } catch (e) {
            console.error('Login error:', e);
            return false;
        }
    },

    async register(email, password, full_name, is_admin = false) {
        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, full_name, is_admin })
            });
            const data = await response.json();
            return { success: response.ok && data.success, message: data.detail };
        } catch (e) {
            console.error('Register error:', e);
            return { success: false, message: 'Сетевая ошибка' };
        }
    },

    async logout() {
        try {
            await fetch('/auth/logout', { method: 'POST' });
            window.location.href = 'login.html';
        } catch (e) {
            console.error('Logout error:', e);
        }
    },

    async checkAuth() {
        try {
            const response = await fetch('/users/me');
            if (response.status === 401) {
                if (!window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html')) {
                    window.location.href = 'login.html';
                }
                return null;
            }
            return await response.json();
        } catch (e) {
            console.error('Auth check error:', e);
            return null;
        }
    }
};

// Проверяем авторизацию при загрузке страницы, кроме страниц входа/регистрации
if (!window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html')) {
    Auth.checkAuth().then(user => {
        if (user) {
            console.log('Authorized as:', user.email);
            // Можно обновить UI с именем пользователя
            const userElem = document.querySelector('.fa-user-circle')?.parentElement;
            if (userElem) {
                userElem.innerHTML = `<i class="fas fa-user-circle mr-1"></i> ${user.full_name} · ${user.is_admin ? 'Admin' : 'Analyst'}`;
            }
        }
    });
}
