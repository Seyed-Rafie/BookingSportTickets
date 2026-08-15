import API from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    // ----------------------------------------------------
    // ۱. بررسی لاگین بودن کاربر
    // ----------------------------------------------------
    if (!API.getToken()) {
        window.location.href = 'login.html'; // کاربر لاگین نیست
        return;
    }

    // انتخاب المنت‌ها
    const reservationsContainer = document.getElementById('reservations-container');
    const profileForm = document.getElementById('profile-form');
    const profileMsg = document.getElementById('profile-msg');
    const logoutBtn = document.getElementById('logout-btn');

    // متغیرهای مدال
    let currentReservationId = null;
    const cancelModal = document.getElementById('cancel-modal');
    const reportModal = document.getElementById('report-modal');
    const cancelDetails = document.getElementById('cancel-details');

    // خروج از حساب
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        API.removeToken();
        window.location.href = 'index.html';
    });

    // ----------------------------------------------------
    // ۲. بارگذاری اطلاعات پروفایل
    // ----------------------------------------------------
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

    // ----------------------------------------------------
    // ۳. آپدیت اطلاعات پروفایل
    // ----------------------------------------------------
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
            profileMsg.innerText = 'اطلاعات با موفقیت بروزرسانی شد.';
            setTimeout(() => profileMsg.style.display = 'none', 3000);
        } catch (error) {
            profileMsg.style.display = 'block';
            profileMsg.style.color = 'var(--danger)';
            profileMsg.innerText = error.message;
        }
    });

    // ----------------------------------------------------
    // ۴. بارگذاری تاریخچه رزروها و بلیط‌ها
    // ----------------------------------------------------
    async function loadReservations() {
        try {
            const reservations = await API.reservations.getMyReservations();
            reservationsContainer.innerHTML = '';

            if (reservations.length === 0) {
                reservationsContainer.innerHTML = '<p>شما هنوز هیچ بلیطی خریداری نکرده‌اید.</p>';
                return;
            }

            reservations.forEach(res => {
                // تعیین رنگ و متن وضعیت
                let statusClass = 'status-reserved';
                let statusText = 'رزرو موقت (در انتظار پرداخت)';
                let actionButtonsHTML = '';

                if (res.status === 'paid') {
                    statusClass = 'status-paid';
                    statusText = 'پرداخت شده / قطعی';
                    actionButtonsHTML = `
                        <button class="btn btn-danger btn-cancel" data-id="${res.reservation_id}">کنسلی و استرداد</button>
                        <button class="btn btn-warning btn-report" data-id="${res.reservation_id}" style="background:var(--warning); color:white;">گزارش مشکل</button>
                    `;
                } else if (res.status === 'cancelled' || res.status === 'expired') {
                    statusClass = 'status-cancelled';
                    statusText = res.status === 'expired' ? 'منقضی شده' : 'لغو شده';
                }

                // تولید صندلی‌ها به صورت رشته
                const seatsInfo = res.seats.map(s => `${s.section} (ردیف ${s.row} صندلی ${s.seat_number})`).join('، ');

                const card = document.createElement('div');
                card.className = `reservation-card ${statusClass}`;
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                        <h3 style="margin:0;">${res.match_title}</h3>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <p><strong>ورزشگاه:</strong> ${res.venue_name}</p>
                    <p><strong>زمان مسابقه:</strong> ${new Date(res.match_datetime).toLocaleString('fa-IR')}</p>
                    <p><strong>صندلی‌ها:</strong> ${seatsInfo}</p>
                    <p><strong>مبلغ کل:</strong> ${Number(res.total_price).toLocaleString('fa-IR')} تومان</p>
                    <div class="action-buttons">
                        ${actionButtonsHTML}
                    </div>
                `;
                reservationsContainer.appendChild(card);
            });

            attachReservationEvents();
        } catch (error) {
            reservationsContainer.innerHTML = `<p style="color:var(--danger);">خطا: ${error.message}</p>`;
        }
    }

    // ----------------------------------------------------
    // ۵. مدیریت رویدادهای کنسلی و گزارش
    // ----------------------------------------------------
    function attachReservationEvents() {
        // کلیک روی دکمه کنسلی
        document.querySelectorAll('.btn-cancel').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                currentReservationId = e.target.getAttribute('data-id');
                cancelDetails.innerHTML = '<p>در حال بررسی شرایط جریمه...</p>';
                cancelModal.classList.add('active');

                try {
                    // فراخوانی API بررسی جریمه (بدون کنسل کردن قطعی)
                    const penaltyData = await API.reservations.checkPenalty(currentReservationId);
                    cancelDetails.innerHTML = `
                        <p>قوانین کنسلی برگزار کننده بررسی شد:</p>
                        <ul>
                            <li><strong>مبلغ پرداختی شما:</strong> ${Number(penaltyData.total_price).toLocaleString('fa-IR')} تومان</li>
                            <li><strong>درصد جریمه اعمال شده:</strong> ${penaltyData.penalty_percentage}٪</li>
                            <li><strong>مبلغی که به کیف پول شما برمی‌گردد:</strong> <span style="color:var(--success); font-weight:bold;">${Number(penaltyData.refund_amount).toLocaleString('fa-IR')} تومان</span></li>
                        </ul>
                        <p style="font-size:0.9rem; color:var(--text-muted); margin-top:1rem;">آیا از استرداد و لغو این بلیط اطمینان دارید؟ این عمل غیرقابل بازگشت است.</p>
                    `;
                } catch (error) {
                    cancelDetails.innerHTML = `<p style="color:var(--danger);">امکان بررسی جریمه وجود ندارد: ${error.message}</p>`;
                }
            });
        });

        // کلیک روی دکمه گزارش مشکل
        document.querySelectorAll('.btn-report').forEach(btn => {
            btn.addEventListener('click', (e) => {
                currentReservationId = e.target.getAttribute('data-id');
                reportModal.classList.add('active');
            });
        });
    }

    // تایید نهایی کنسلی
    document.getElementById('confirm-cancel-btn').addEventListener('click', async () => {
        try {
            await API.reservations.cancel(currentReservationId);
            alert('کنسلی با موفقیت انجام شد و مبلغ به کیف پول شما واریز گردید.');
            cancelModal.classList.remove('active');
            loadReservations(); // رفرش لیست بلیط‌ها
        } catch (error) {
            alert('خطا در کنسلی: ' + error.message);
        }
    });

    // سابمیت فرم گزارش مشکل
    document.getElementById('report-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const reportData = {
            reservation_id: parseInt(currentReservationId),
            category: document.getElementById('report-category').value,
            description: document.getElementById('report-description').value
        };

        try {
            await API.reports.submit(reportData);
            alert('گزارش شما با موفقیت ثبت شد و توسط پشتیبانی بررسی خواهد شد.');
            reportModal.classList.remove('active');
            e.target.reset(); // پاک کردن فرم
        } catch (error) {
            alert('خطا در ثبت گزارش: ' + error.message);
        }
    });

    // بستن مدال‌ها
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            cancelModal.classList.remove('active');
            reportModal.classList.remove('active');
        });
    });

    // ----------------------------------------------------
    // اجرا در هنگام لود
    // ----------------------------------------------------
    loadProfile();
    loadReservations();
});
