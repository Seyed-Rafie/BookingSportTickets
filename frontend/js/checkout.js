import API from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    // ----------------------------------------------------
    // ۱. بررسی لاگین و استخراج شناسه رزرو از URL
    // ----------------------------------------------------
    if (!API.getToken()) {
        alert('لطفاً ابتدا وارد حساب کاربری خود شوید.');
        window.location.href = 'login.html';
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const reservationId = urlParams.get('reservation_id');

    if (!reservationId) {
        alert('شناسه رزرو نامعتبر است.');
        window.location.href = 'index.html';
        return;
    }

    // ----------------------------------------------------
    // ۲. المان‌های DOM
    // ----------------------------------------------------
    const summaryContent = document.getElementById('summary-content');
    const timerDisplay = document.getElementById('timer-display');
    const timerBox = document.getElementById('reservation-timer');
    const cardNumberInput = document.getElementById('card-number');
    const expMonthInput = document.getElementById('exp-month');
    const expYearInput = document.getElementById('exp-year');
    const cvv2Input = document.getElementById('cvv2');
    const otpInput = document.getElementById('otp-code');
    const sendOtpBtn = document.getElementById('send-otp-btn');
    const paymentForm = document.getElementById('payment-form');
    const submitPayBtn = document.getElementById('submit-pay-btn');
    const paymentMsg = document.getElementById('payment-msg');

    let currentReservation = null;
    let mainTimerInterval = null;
    let otpTimerInterval = null;
    let isProcessing = false;   // جلوگیری از ارسال دوباره فرم
    let paymentVerified = false; // فلگ تأیید نهایی پرداخت

    // ----------------------------------------------------
    // ۳. بارگذاری اطلاعات رزرو
    // ----------------------------------------------------
    async function loadReservationDetails() {
        try {
            const myReservations = await API.reservations.getMyReservations();
            currentReservation = myReservations.find(
                r => r.reservation_id == reservationId || r.id == reservationId
            );

            if (!currentReservation) {
                throw new Error('اطلاعات رزرو یافت نشد یا منقضی شده است.');
            }

            // اگر رزرو قبلاً پرداخت شده، نیازی به این صفحه نیست
            if (currentReservation.status === 'paid') {
                showMessage('این رزرو قبلاً با موفقیت پرداخت شده است.', 'success');
                setTimeout(() => {
                    window.location.href = 'profile.html';
                }, 1500);
                return;
            }

            // اگر رزرو لغو یا منقضی شده
            if (currentReservation.status === 'cancelled' || currentReservation.status === 'expired') {
                throw new Error(`این رزرو ${currentReservation.status === 'cancelled' ? 'لغو' : 'منقضی'} شده است.`);
            }

            renderSummary(currentReservation);
            startMainTimer(600); // ۱۰ دقیقه مهلت رزرو موقت
        } catch (error) {
            summaryContent.innerHTML = `<p style="color:red; text-align:center;">${error.message}</p>`;
            disableForm();
        }
    }

    function renderSummary(res) {
        let seatsInfo = 'عمومی';
        if (res.seats && res.seats.length > 0) {
            seatsInfo = res.seats.map(s => 
                `بخش ${s.section} (ردیف ${s.row} - صندلی ${s.seat_number})`
            ).join('<br>');
        }

        summaryContent.innerHTML = `
            <div class="summary-item">
                <span>رویداد:</span>
                <strong>${res.match_title || 'مسابقه ورزشی'}</strong>
            </div>
            <div class="summary-item">
                <span>ورزشگاه:</span>
                <span>${res.venue_name || 'نامشخص'}</span>
            </div>
            <div class="summary-item">
                <span>تاریخ برگزاری:</span>
                <span>${new Date(res.match_datetime).toLocaleString('fa-IR')}</span>
            </div>
            <div class="summary-item">
                <span>صندلی‌ها:</span>
                <span style="text-align: left; font-size: 0.85rem;">${seatsInfo}</span>
            </div>
            <div class="summary-total">
                <span>مبلغ قابل پرداخت:</span>
                <span>${Number(res.total_price || 0).toLocaleString('fa-IR')} تومان</span>
            </div>
        `;
    }

    function disableForm() {
        cardNumberInput.disabled = true;
        expMonthInput.disabled = true;
        expYearInput.disabled = true;
        cvv2Input.disabled = true;
        otpInput.disabled = true;
        sendOtpBtn.disabled = true;
        submitPayBtn.disabled = true;
    }

    // ----------------------------------------------------
    // ۴. تایمر شمارش معکوس ۱۰ دقیقه
    // ----------------------------------------------------
    function startMainTimer(durationInSeconds) {
        let timer = durationInSeconds;
        mainTimerInterval = setInterval(() => {
            const minutes = parseInt(timer / 60, 10);
            const seconds = parseInt(timer % 60, 10);

            const displayMin = minutes < 10 ? '0' + minutes : minutes;
            const displaySec = seconds < 10 ? '0' + seconds : seconds;

            timerDisplay.textContent = `${displayMin}:${displaySec}`;

            if (--timer < 0) {
                clearInterval(mainTimerInterval);
                timerBox.classList.add('expired');
                timerDisplay.textContent = 'منقضی شد!';
                disableForm();
                showMessage('⚠ زمان رزرو موقت شما به پایان رسید. لطفاً از ابتدا صندلی‌ها را انتخاب کنید.', 'danger');
            }
        }, 1000);
    }

    // ----------------------------------------------------
    // ۵. فرمت‌دهی خودکار شماره کارت (4-4-4-4)
    // ----------------------------------------------------
    cardNumberInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        value = value.substring(0, 16);
        let formatted = '';
        for (let i = 0; i < value.length; i++) {
            if (i > 0 && i % 4 === 0) formatted += ' - ';
            formatted += value[i];
        }
        e.target.value = formatted;

        // پاک کردن OTP در صورت تغییر کارت
        if (otpInput.value) {
            otpInput.value = '';
            otpInput.disabled = true;
            resetOtpButton();
        }
    });

    // فقط عدد برای فیلدهای عددی
    [expMonthInput, expYearInput, cvv2Input, otpInput].forEach(input => {
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    });

    // محدودسازی ماه به 01-12
    expMonthInput.addEventListener('blur', () => {
        const m = parseInt(expMonthInput.value);
        if (m && (m < 1 || m > 12)) {
            showMessage('ماه انقضا باید بین 01 تا 12 باشد.', 'danger');
            expMonthInput.focus();
        }
    });

    // ----------------------------------------------------
    // ۶. اعتبارسنجی اطلاعات کارت قبل از درخواست OTP
    // ----------------------------------------------------
    function validateCardInfo() {
        const rawCard = cardNumberInput.value.replace(/\D/g, '');
        if (rawCard.length !== 16) {
            showMessage('شماره کارت بانکی باید ۱۶ رقم باشد.', 'danger');
            cardNumberInput.focus();
            return false;
        }

        if (!luhnCheck(rawCard)) {
            showMessage('شماره کارت بانکی معتبر نیست (خطا در الگوریتم Luhn).', 'danger');
            cardNumberInput.focus();
            return false;
        }

        const month = parseInt(expMonthInput.value);
        const year = parseInt(expYearInput.value);
        if (!month || month < 1 || month > 12) {
            showMessage('ماه انقضا نامعتبر است (01 تا 12).', 'danger');
            expMonthInput.focus();
            return false;
        }
        if (!year || year < 1 || year > 99) {
            showMessage('سال انقضا نامعتبر است.', 'danger');
            expYearInput.focus();
            return false;
        }

        if (!cvv2Input.value || cvv2Input.value.length < 3) {
            showMessage('کد CVV2 باید حداقل ۳ رقم باشد.', 'danger');
            cvv2Input.focus();
            return false;
        }

        return true;
    }

    // الگوریتم Luhn برای اعتبارسنجی شماره کارت
    function luhnCheck(cardNumber) {
        let sum = 0;
        let isEven = false;
        for (let i = cardNumber.length - 1; i >= 0; i--) {
            let digit = parseInt(cardNumber[i]);
            if (isEven) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            sum += digit;
            isEven = !isEven;
        }
        return sum % 10 === 0;
    }

    // ----------------------------------------------------
    // ۷. درخواست رمز پویا (OTP)
    // ----------------------------------------------------
    sendOtpBtn.addEventListener('click', async () => {
        if (!validateCardInfo()) return;

        const rawCard = cardNumberInput.value.replace(/\D/g, '');

        sendOtpBtn.disabled = true;
        sendOtpBtn.textContent = 'در حال ارسال...';

        try {
            // اصلاح شده: استفاده از API.reservations
            await API.reservations.requestOtp(reservationId, rawCard);

            showMessage('✅ کد رمز پویا به شماره همراه ثبت‌شده در بانک پیامک شد.', 'success');
            otpInput.disabled = false;
            otpInput.focus();

            startOtpResendTimer(120);
        } catch (error) {
            showMessage(`❌ خطا در ارسال رمز پویا: ${error.message}`, 'danger');
            resetOtpButton();
        }
    });

    function startOtpResendTimer(seconds) {
        let countdown = seconds;
        sendOtpBtn.classList.add('requested');

        otpTimerInterval = setInterval(() => {
            const min = parseInt(countdown / 60);
            const sec = countdown % 60;
            sendOtpBtn.textContent = `ارسال مجدد (${min}:${sec < 10 ? '0' + sec : sec})`;

            if (--countdown < 0) {
                clearInterval(otpTimerInterval);
                resetOtpButton();
            }
        }, 1000);
    }

    function resetOtpButton() {
        clearInterval(otpTimerInterval);
        sendOtpBtn.disabled = false;
        sendOtpBtn.classList.remove('requested');
        sendOtpBtn.textContent = 'درخواست رمز پویا';
    }

    // ----------------------------------------------------
    // ۸. ثبت فرم پرداخت نهایی
    // ----------------------------------------------------
    paymentForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (isProcessing || paymentVerified) return;

        if (!validateCardInfo()) return;

        if (!otpInput.value || otpInput.value.length < 4) {
            showMessage('کد رمز پویا را به درستی وارد کنید.', 'danger');
            otpInput.focus();
            return;
        }

        if (timerDisplay.textContent === 'منقضی شد!') {
            showMessage('زمان رزرو موقت به پایان رسیده است.', 'danger');
            return;
        }

        isProcessing = true;
        submitPayBtn.disabled = true;
        submitPayBtn.innerHTML = 'در حال پردازش و استعلام از بانک<span class="loading-spinner"></span>';

        const paymentData = {
            reservation_id: parseInt(reservationId), // اضافه شدن شناسه رزرو
            card_number: cardNumberInput.value.replace(/\D/g, ''),
            expiry_month: expMonthInput.value,
            expiry_year: expYearInput.value,
            cvv2: cvv2Input.value,
            otp_code: otpInput.value
        };

        try {
            // اصلاح شده: استفاده از API.reservations
            const result = await API.reservations.pay(paymentData);

            // توقف تایمرها و قفل کردن فرم
            clearInterval(mainTimerInterval);
            clearInterval(otpTimerInterval);
            paymentVerified = true;
            disableForm();

            showMessage('✅ پرداخت با موفقیت انجام شد. در حال انتقال به پروفایل...', 'success');

            // انتقال به صفحه پروفایل یا رسید
            setTimeout(() => {
                window.location.href = `profile.html?payment=success&reservation_id=${reservationId}`;
            }, 2000);

        } catch (error) {
            isProcessing = false;
            submitPayBtn.disabled = false;
            submitPayBtn.textContent = 'تکمیل پرداخت و رزرو قطعی';
            showMessage(`❌ پرداخت ناموفق: ${error.message || 'خطایی در ارتباط با سرور رخ داده است.'}`, 'danger');
            
            // پاک کردن کد OTP در صورت خطا
            otpInput.value = '';
            otpInput.disabled = true;
            resetOtpButton();
        }
    });

    // ----------------------------------------------------
    // ۹. تابع نمایش پیام‌های سیستم
    // ----------------------------------------------------
    function showMessage(message, type = 'danger') {
        if (!paymentMsg) return;
        paymentMsg.textContent = message;
        paymentMsg.className = `alert alert-${type}`;
        paymentMsg.style.display = 'block';
    }

    // بارگذاری اولیه اطلاعات رزرو
    await loadReservationDetails();
});