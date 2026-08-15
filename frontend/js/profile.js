import API from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    // چک کردن لاگین با تابعی که الان به API اضافه کردیم
    if (!API.getToken()) {
        window.location.href = 'login.html'; 
        return;
    }

    const reservationsContainer = document.getElementById('reservations-container');
    const profileForm = document.getElementById('profile-form');
    const profileMsg = document.getElementById('profile-msg');
    
    let currentReservationId = null;
    const cancelModal = document.getElementById('cancel-modal');
    const reportModal = document.getElementById('report-modal');
    const cancelDetails = document.getElementById('cancel-details');

    document.getElementById('logout-btn').addEventListener('click', (e) => {
        e.preventDefault();
        API.removeToken();
        window.location.href = 'index.html';
    });

    // بارگذاری پروفایل
    async function loadProfile() {
        try {
            const user = await API.auth.getProfile();
            document.getElementById('user-name').value = user.full_name || '';
            document.getElementById('user-phone').value = user.phone || '';
            document.getElementById('user-email').value = user.email || '';
            document.getElementById('user-city').value = user.city || '';
        } catch (error) {
            console.error('خطا در دریافت پروفایل:', error);
        }
    }

    // ویرایش پروفایل
    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userData = {
            full_name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            city: document.getElementById('user-city').value
        };

        try {
            await API.auth.updateProfile(userData);
            profileMsg.style.display = 'block';
            profileMsg.style.color = 'var(--success)';
            profileMsg.innerText = 'اطلاعات بروزرسانی شد.';
            setTimeout(() => profileMsg.style.display = 'none', 3000);
        } catch (error) {
            profileMsg.style.display = 'block';
            profileMsg.style.color = 'var(--danger)';
            profileMsg.innerText = error.message;
        }
    });

    // بارگذاری تاریخچه
    async function loadReservations() {
        try {
            const reservations = await API.reservations.getMyReservations();
            reservationsContainer.innerHTML = '';

            if (!reservations || reservations.length === 0) {
                reservationsContainer.innerHTML = '<p>تاریخچه خریدی یافت نشد.</p>';
                return;
            }

            reservations.forEach(res => {
                let statusClass = 'status-reserved';
                let statusText = 'در انتظار پرداخت';
                let actionBtns = '';

                if (res.status === 'paid') {
                    statusClass = 'status-paid';
                    statusText = 'پرداخت شده';
                    actionBtns = `
                        <button class="btn btn-danger btn-cancel" data-id="${res.reservation_id}">کنسلی</button>
                        <button class="btn btn-warning btn-report" data-id="${res.reservation_id}" style="background:var(--warning); color:white;">گزارش مشکل</button>
                    `;
                } else if (res.status === 'cancelled' || res.status === 'expired') {
                    statusClass = 'status-cancelled';
                    statusText = 'لغو شده';
                }

                const card = document.createElement('div');
                card.className = `reservation-card ${statusClass}`;
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between;">
                        <h3>${res.match_title || 'بلیط مسابقه'}</h3>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <p>مبلغ: ${Number(res.total_price).toLocaleString('fa-IR')} تومان</p>
                    <div class="action-buttons">${actionBtns}</div>
                `;
                reservationsContainer.appendChild(card);
            });

            // اتصال دکمه‌های کنسلی و گزارش
            document.querySelectorAll('.btn-cancel').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    currentReservationId = e.target.getAttribute('data-id');
                    cancelModal.classList.add('active');
                    cancelDetails.innerHTML = 'در حال محاسبه جریمه...';
                    try {
                        const penaltyData = await API.reservations.checkPenalty(currentReservationId);
                        cancelDetails.innerHTML = `جریمه: ${penaltyData.penalty_percentage}٪ <br> مبلغ بازگشتی: ${penaltyData.refund_amount} تومان`;
                    } catch (err) {
                        cancelDetails.innerHTML = `<p style="color:red;">خطا: ${err.message}</p>`;
                    }
                });
            });

            document.querySelectorAll('.btn-report').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    currentReservationId = e.target.getAttribute('data-id');
                    reportModal.classList.add('active');
                });
            });

        } catch (error) {
            reservationsContainer.innerHTML = `<p style="color:var(--danger);">خطا: ${error.message}</p>`;
        }
    }

    // تایید کنسلی
    document.getElementById('confirm-cancel-btn').addEventListener('click', async () => {
        try {
            await API.reservations.cancel(currentReservationId);
            alert('بلیط کنسل شد.');
            cancelModal.classList.remove('active');
            loadReservations();
        } catch (error) {
            alert('خطا: ' + error.message);
        }
    });

    // ثبت گزارش
    document.getElementById('report-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            await API.reports.submit({
                reservation_id: parseInt(currentReservationId),
                category: document.getElementById('report-category').value,
                description: document.getElementById('report-description').value
            });
            alert('گزارش ثبت شد.');
            reportModal.classList.remove('active');
            e.target.reset();
        } catch (error) {
            alert('خطا: ' + error.message);
        }
    });

    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            cancelModal.classList.remove('active');
            reportModal.classList.remove('active');
        });
    });

    loadProfile();
    loadReservations();
});
