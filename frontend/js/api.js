// if it deployed on a server, this must change
const BASE_URL = 'http://127.0.0.1:8001';

/**
 * ساخت هدرهای سفارشی به همراه توکن JWT (در صورت وجود در localStorage)
 */
function getHeaders(customHeaders = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...customHeaders
    };

    const token = localStorage.getItem('token');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
}

/**
 * تابع اصلی برای ارسال درخواست‌های شبکه (Wrapper روی fetch)
 */
async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;

    const { headers: customHeaders, body: rawBody, ...restOptions } = options;

    const config = {
        method: 'GET',
        ...restOptions,
        headers: getHeaders(customHeaders)
    };

    // تبدیل اتوماتیک بدنه درخواست به فرمت JSON
    if (rawBody) {
        config.body = typeof rawBody === 'object' ? JSON.stringify(rawBody) : rawBody;
    }

    try {
        const response = await fetch(url, config);

        // اگر توکن منقضی یا نامعتبر بود (401 Unauthorized)، توکن پاک می‌شود
        if (response.status === 401) {
            localStorage.removeItem('token');
        }

        // استخراج پاسخ JSON (در صورت خالی بودن پاسخ، یک شیء خالی برمی‌گرداند)
        const data = await response.json().catch(() => ({}));

        // اگر وضعیت HTTP در بازه 200 تا 299 نبود
        if (!response.ok) {
            const errorMessage = data.detail || `خطای سرور (کد ${response.status})`;
            throw new Error(errorMessage);
        }

        return data;

    } catch (error) {
        console.error(`[API Error] ${config.method} ${endpoint}:`, error.message);
        throw error;
    }
}

/**
 * ماژول اصلی API جهت بازاستفاده در تمام فایل‌های پروژه
 */
const API = {
    // توابع مدیریت توکن
    getToken: () => localStorage.getItem('token'),
    setToken: (token) => localStorage.setItem('token', token),
    removeToken: () => localStorage.removeItem('token'),

    // -------------------------------------------------------------
    // ۱. احراز هویت و مدیریت کاربران
    // -------------------------------------------------------------
    auth: {
        sendOTP: (phoneNumber) => 
            request('/auth/send-otp', { method: 'POST', body: { identifier: phoneNumber } }),

        verifyOTP: (phoneNumber, code) => 
            request('/auth/verify-otp', { method: 'POST', body: { identifier: phoneNumber, code } }),

        login: (credentials) => 
            request('/auth/login', { method: 'POST', body: credentials }),

        getProfile: () => 
            request('/users/me', { method: 'GET' }),

        updateProfile: (profileData) => 
            request('/users/me', { method: 'PATCH', body: profileData }),
    },

    // -------------------------------------------------------------
    // ۲. جستجو و نمایش بلیط‌ها (متصل به Elasticsearch در بک‌اند)
    // -------------------------------------------------------------
    tickets: {
        search: (params = {}) => {
            const cleanParams = {};
            Object.keys(params).forEach(key => {
                if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                    cleanParams[key] = params[key];
                }
            });

            const queryString = new URLSearchParams(cleanParams).toString();
            const endpoint = queryString ? `/tickets/?${queryString}` : '/tickets/';
            return request(endpoint, { method: 'GET' });
        },

        getDetails: (ticketId) => 
            request(`/tickets/${ticketId}`, { method: 'GET' }),

        getVenues: () => 
            request('/venues', { method: 'GET' }),
    }, // <-- بخش تکراری و خراب اینجا حذف شد

    // -------------------------------------------------------------
    // ۳. رزرو، پرداخت و کنسلی
    // -------------------------------------------------------------
    reservations: {
        create: (ticketId, quantity = 1) => 
            request('/reservations', { method: 'POST', body: { ticket_id: ticketId, quantity } }),

        pay: (reservationId) => 
            request(`/payments/${reservationId}`, { method: 'POST' }),

        getMyReservations: () => 
            request('/reservations/me', { method: 'GET' }),

        checkPenalty: (reservationId) => 
            request(`/cancellations/penalty-check?reservation_id=${reservationId}`, { method: 'GET' }),

        cancel: (reservationId) => 
            request(`/reservations/${reservationId}/cancel`, { method: 'POST' }),
    },

    // -------------------------------------------------------------
    // ۴. پشتیبانی و گزارش‌ها
    // -------------------------------------------------------------
    reports: {
        submit: (reportData) => 
            request('/reports', { method: 'POST', body: reportData }),
    }
};

// هر دو روش Export را نگه می‌داریم تا هم فایل‌های شما کار کند و هم فایل‌های هم‌تیمی‌تان
export default API;
window.API = API;
