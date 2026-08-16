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
            let errorMessage = `خطای سرور (کد ${response.status})`;

            if (typeof data.detail === 'string') {
                errorMessage = data.detail;
            } else if (Array.isArray(data.detail)) {
                // استخراج پیام‌های خطای اعتبارسنجی (Validation Errors) در FastAPI
                errorMessage = data.detail.map(err => err.msg || 'خطای ورودی').join(' | ');
            } else if (data.message) {
                errorMessage = data.message;
            }

            throw new Error(errorMessage);
        }

        return data;

    } catch (error) {
        console.error(`[API Error] ${config.method} ${endpoint}:`, error.message);
        throw error;
    }
}

/**
 * کمک‌کننده برای یکسان‌سازی فرمت داده‌های OTP
 */
function normalizeOtpPayload(payload, secondaryParam) {
    if (typeof payload === 'object' && payload !== null) {
        return payload;
    }
    if (secondaryParam !== undefined) {
        return { identifier: payload, code: secondaryParam };
    }
    return { identifier: payload };
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
        sendOTP: (payload) => 
            request('/auth/send-otp', { method: 'POST', body: normalizeOtpPayload(payload) }),

        verifyOTP: (payload, code) => 
            request('/auth/verify-otp', { method: 'POST', body: normalizeOtpPayload(payload, code) }),

        signup: (signupData) => 
            request('/auth/signup', { method: 'POST', body: signupData }),

        login: (credentials) => 
            request('/auth/login', { method: 'POST', body: credentials }),

        getProfile: () => 
            request('/users/me', { method: 'GET' }),

        updateProfile: (profileData) => 
            request('/users/me', { method: 'PATCH', body: profileData }),
    },

    // -------------------------------------------------------------
    // ۲. مدیریت پروفایل کاربر (منطبق بر users.py)
    // -------------------------------------------------------------
    users: {
        getProfile: () => 
            request('/users/me', { method: 'GET' }),

        updateProfile: (profileData) => 
            request('/users/me', { method: 'PATCH', body: profileData }),
    },

    // -------------------------------------------------------------
    // ۳. جستجو و نمایش بلیط‌ها (متصل به Elasticsearch در بک‌اند)
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
    // ۴. رزرو، پرداخت و کنسلی
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
    // ۵. پشتیبانی و گزارش‌ها
    // -------------------------------------------------------------
    reports: {
        submit: (reportData) => 
            request('/reports', { method: 'POST', body: reportData }),
    },

    // -------------------------------------------------------------
    // ۶. پنل ادمین (منطبق بر admin.py)
    // -------------------------------------------------------------
    admin: {
        getReports: (status = null) => {
            const endpoint = status ? `/admin/reports?status=${status}` : '/admin/reports';
            return request(endpoint, { method: 'GET' });
        },

        respondToReport: (reportId, payload) => 
            request(`/admin/reports/${reportId}`, { method: 'PATCH', body: payload }),

        updateReservationStatus: (reservationId, payload) => 
            request(`/admin/reservations/${reservationId}`, { method: 'PATCH', body: payload }),
    }
};

// هر دو روش Export را نگه می‌داریم تا هم فایل‌های شما کار کند و هم فایل‌های هم‌تیمی‌تان
export default API;
window.API = API;