import API from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // ۱. بررسی احراز هویت اولیه
    // ----------------------------------------------------
    if (!API.getToken()) {
        alert('لطفاً ابتدا وارد حساب کاربری خود شوید.');
        window.location.href = 'login.html'; 
        return;
    }

    // ----------------------------------------------------
    // DOM Elements
    // ----------------------------------------------------
    const profileForm = document.getElementById('profile-form');
    const profileMsg = document.getElementById('profile-msg');
    const reservationsContainer = document.getElementById('reservations-container');
    const logoutBtn = document.getElementById('logout-btn');

    const cancelModal = document.getElementById('cancel-modal');
    const cancelDetails = document.getElementById('cancel-details');
    const confirmCancelBtn = document.getElementById('confirm-cancel-btn');

    const reportModal = document.getElementById('report-modal');
    const reportForm = document.getElementById('report-form');

    let selectedReservationId = null; // برای ذخیره شناسه رزروی که در مدال باز است

    // ----------------------------------------------------
    // خروج از حساب
    // ----------------------------------------------------
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        API.removeToken();
        window.location.href = 'index.html';
    });

    // ----------------------------------------------------
    // ۲. بارگذاری و ویرایش پروفایل کاربر
    // ----------------------------------------------------
    async function initProfile() {
        try {
            const profileData = await API.auth.getProfile();
            document.getElementById('user-name').value = profileData.full_name || '';
            document.getElementById('user-phone').value = profileData.phone || profileData.identifier || '';
            document.getElementById('user-email').value = profileData.email || '';
            document.getElementById('user-city').value = profileData.city || '';
        } catch (error) {
            showProfileMessage(error.message, 'danger');
        }
    }

    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const updateData = {
            full_name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            city: document.getElementById('user-city').value
        };

        try {
            await API.auth.updateProfile(updateData);
            showProfileMessage('اطلاعات حساب کاربری با موفقیت بروزرسانی شد.', 'success');
        } catch (error) {
            showProfileMessage(`خطا در ویرایش پروفایل: ${error.message}`, 'danger');
        }
    });

    function showProfileMessage(msg, type) {
        profileMsg.textContent = msg;
        profileMsg.className = `alert alert-${type}`;
        profileMsg.style.display = 'block';
        setTimeout(() => { profileMsg.style.display = 'none'; }, 4000);
    }

    // ----------------------------------------------------
    // ۳. بارگذاری لیست بلیط‌ها و رزروها
    // ----------------------------------------------------
    async function loadReservations() {
        try {
            const reservations = await API.reservations.getMyReservations();
            reservationsContainer.innerHTML = '';

            if (!reservations || reservations.length === 0) {
                reservationsContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted);">شما هنوز هیچ بلیطی خریداری یا رزرو نکرده‌اید.</p>';
                return;
            }

            reservations.forEach(res => {
                // استخراج اطلاعات صندلی‌ها
                let seatsInfo = 'نامشخص';
                if (res.seats && res.seats.length > 0) {
                    seatsInfo = res.seats.map(s => `${s.section} (ردیف ${s.row} صندلی ${s.seat_number})`).join('، ');
                }

                // تنظیم کلاس‌ها و متن‌های وضعیت
                let statusClass = 'status-reserved';
                let statusText = 'رزرو موقت (در انتظار پرداخت)';
                let actionsHtml = '';

                if (res.status === 'paid') {
                    statusClass = 'status-paid';
                    statusText = 'پرداخت شده / قطعی';
                    actionsHtml = `
                        <button class="btn btn-danger open-cancel-modal" data-id="${res.reservation_id}">کنسلی و استرداد</button>
                        <button class="btn btn-warning open-report-modal" data-id="${res.reservation_id}">گزارش مشکل</button>
                    `;
                } else if (res.status === 'cancelled' || res.status === 'expired') {
                    statusClass = 'status-cancelled';
                    statusText = (res.status === 'expired') ? 'منقضی شده' : 'لغو شده';
                }

                // ساخت کارت رزرو
                const card = document.createElement('div');
                card.className = `reservation-card ${statusClass}`;
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 1rem;">
                        <h3 style="margin: 0;">${res.match_title || 'مسابقه ورزشی'}</h3>
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </div>
                    <p><strong>ورزشگاه:</strong> ${res.venue_name || 'نامشخص'}</p>
                    <p><strong>زمان مسابقه:</strong> ${new Date(res.match_datetime).toLocaleString('fa-IR')}</p>
                    <p><strong>صندلی‌های انتخابی:</strong> ${seatsInfo}</p>
                    <p><strong>مبلغ کل:</strong> ${Number(res.total_price).toLocaleString('fa-IR')} تومان</p>
                    <div class="action-buttons">
                        ${actionsHtml}
                    </div>
                `;
                reservationsContainer.appendChild(card);
            });

            bindCardActionButtons(); // متصل کردن Event Listener ها به دکمه‌های جدید
        } catch (error) {
            reservationsContainer.innerHTML = `<p style="color:var(--danger); text-align:center;">خطا در دریافت تاریخچه بلیط‌ها: ${error.message}</p>`;
        }
    }

    // ----------------------------------------------------
    // ۴. مدیریت مدال‌ها، کنسلی و گزارش
    // ----------------------------------------------------
    function bindCardActionButtons() {
        // باز کردن مدال بررسی جریمه
        document.querySelectorAll('.open-cancel-modal').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                selectedReservationId = e.target.getAttribute('data-id');
                cancelModal.classList.add('active');
                confirmCancelBtn.disabled = true;
                cancelDetails.innerHTML = '<p>در حال استعلام قوانین کنسلی از سرور...</p>';

                try {
                    const penaltyData = await API.reservations.checkPenalty(selectedReservationId);
                    cancelDetails.innerHTML = `
                        <p><strong>مبلغ پرداخت شده:</strong> ${Number(penaltyData.total_price || 0).toLocaleString('fa-IR')} تومان</p>
                        <p><strong>درصد جریمه اعمالی:</strong> ${penaltyData.penalty_percentage || 0}٪</p>
                        <p style="margin-top: 0.5rem; font-size: 1.1rem;">
                            <strong>مبلغ بازگشتی به کیف پول:</strong> 
                            <span style="color: var(--success); font-weight: bold;">${Number(penaltyData.refund_amount || 0).toLocaleString('fa-IR')} تومان</span>
                        </p>
                        <p style="margin-top: 1rem; font-size: 0.9rem; color: var(--text-muted);">
                            آیا از لغو این بلیط اطمینان دارید؟ این عملیات غیرقابل بازگشت است.
                        </p>
                    `;
                    confirmCancelBtn.disabled = false;
                } catch (error) {
                    cancelDetails.innerHTML = `<p style="color: var(--danger);">خطا در استعلام جریمه: ${error.message}</p>`;
                }
            });
        });

        // باز کردن مدال گزارش مشکل
        document.querySelectorAll('.open-report-modal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                selectedReservationId = e.target.getAttribute('data-id');
                reportForm.reset();
                reportModal.classList.add('active');
            });
        });
    }

    // تایید نهایی کنسلی بلیط
    confirmCancelBtn.addEventListener('click', async () => {
        if (!selectedReservationId) return;
        confirmCancelBtn.disabled = true;
        confirmCancelBtn.textContent = 'در حال پردازش...';

        try {
            await API.reservations.cancel(selectedReservationId);
            alert('کنسلی با موفقیت انجام شد و مبلغ به کیف پول شما واریز گردید.');
            cancelModal.classList.remove('active');
            loadReservations(); // بروزرسانی لیست
        } catch (error) {
            alert(`خطا در لغو بلیط: ${error.message}`);
        } finally {
            confirmCancelBtn.textContent = 'تایید نهایی و لغو بلیط';
        }
    });

    // ثبت گزارش مشکل
    reportForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = reportForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'در حال ارسال...';

        const reportData = {
            reservation_id: parseInt(selectedReservationId),
            category: document.getElementById('report-category').value,
            description: document.getElementById('report-description').value
        };

        try {
            await API.reports.submit(reportData);
            alert('گزارش شما با موفقیت ثبت شد. تیم پشتیبانی به زودی آن را بررسی خواهد کرد.');
            reportModal.classList.remove('active');
            reportForm.reset();
        } catch (error) {
            alert(`خطا در ثبت گزارش: ${error.message}`);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'ارسال گزارش';
        }
    });

    // بستن مدال‌ها با کلیک روی دکمه‌های انصراف یا کلیک بیرون کادر
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            cancelModal.classList.remove('active');
            reportModal.classList.remove('active');
        });
    });

    // ----------------------------------------------------
    // شروع چرخه حیات صفحه
    // ----------------------------------------------------
    initProfile();
    loadReservations();
});
