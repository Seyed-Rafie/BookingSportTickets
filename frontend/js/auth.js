document.addEventListener('DOMContentLoaded', () => {
    const formSendOtp = document.getElementById('form-send-otp');
    const formVerifyOtp = document.getElementById('form-verify-otp');
    const mobileInput = document.getElementById('mobile');
    const otpInput = document.getElementById('otp-code');
    const displayMobile = document.getElementById('display-mobile');
    const btnBack = document.getElementById('btn-back');
    const messageBox = document.getElementById('message-box');

    // اگر کاربر قبلاً لاگین کرده بود، انتقال به صفحه اصلی
    if (localStorage.getItem('token')) {
        window.location.href = 'index.html';
        return;
    }

    // تابع نمایش پیام‌های خطا و موفقیت
    function showMessage(msg, isError = true) {
        messageBox.textContent = msg;
        messageBox.className = `message-box ${isError ? 'error' : 'success'}`;
        messageBox.classList.remove('hidden');
    }

    // Regex برای اعتبارسنجی شماره موبایل ایران
    const iranMobileRegex = /^09\d{9}$/;

    // مرحله ۱: ارسال درخواست دریافت کد OTP
    formSendOtp.addEventListener('submit', async (e) => {
        e.preventDefault();
        const mobile = mobileInput.value.trim();

        if (!mobile) {
            showMessage('لطفاً شماره موبایل را وارد کنید.');
            return;
        }

        if (!iranMobileRegex.test(mobile)) {
            showMessage('فرمت شماره موبایل صحیح نیست (مثال: 09123456789)');
            return;
        }

        const submitBtn = document.getElementById('btn-send-otp');
        submitBtn.disabled = true;
        submitBtn.textContent = 'در حال ارسال...';

        try {
            // فراخوانی متمرکز از طریق API.auth (که identifier را خودش تنظیم می‌کند)
            const response = await API.auth.sendOTP(mobile);

            displayMobile.textContent = mobile;
            formSendOtp.classList.add('hidden');
            formVerifyOtp.classList.remove('hidden');
            showMessage(response?.message || 'کد تایید ارسال شد.', false);
            otpInput.focus();
        } catch (error) {
            // خطاهای HTTP که از api.js پرتاب می‌شوند در catch دریافت می‌شوند
            showMessage(error.message || 'خطا در ارسال کد تایید.');
            console.error('Send OTP Error:', error);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'ارسال کد تایید';
        }
    });

    // مرحله ۲: تایید کد OTP و دریافت توکن JWT یا هدایت به ثبت‌نام
    formVerifyOtp.addEventListener('submit', async (e) => {
        e.preventDefault();
        const mobile = mobileInput.value.trim();
        const code = otpInput.value.trim();

        if (!code) {
            showMessage('لطفاً کد تایید را وارد کنید.');
            return;
        }

        const submitBtn = document.getElementById('btn-verify-otp');
        submitBtn.disabled = true;
        submitBtn.textContent = 'در حال بررسی...';

        try {
            // فراخوانی متمرکز تایید کد
            const response = await API.auth.verifyOTP(mobile, code);

            if (response?.access_token) {
                // ۱. کاربر قدیمی -> ذخیره توکن و ورود به صفحه اصلی
                localStorage.setItem('token', response.access_token);
                showMessage('ورود با موفقیت انجام شد. در حال انتقال...', false);

                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1000);
            } else if (response?.is_new_user) {
                // ۲. کاربر جدید -> ذخیره شماره و انتقال به صفحه تکمیل ثبت‌نام
                localStorage.setItem('signup_identifier', mobile);
                showMessage('کد تایید شد. در حال انتقال به تکمیل ثبت‌نام...', false);

                setTimeout(() => {
                    window.location.href = 'signup.html';
                }, 1000);
            } else {
                showMessage(response?.message || 'پاسخ معتبری از سرور دریافت نشد.');
            }
        } catch (error) {
            showMessage(error.message || 'کد تایید اشتباه است یا منقضی شده است.');
            console.error('Verify OTP Error:', error);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'تایید و ورود';
        }
    });

    // بازگشت به فرم شماره موبایل
    btnBack.addEventListener('click', () => {
        formVerifyOtp.classList.add('hidden');
        formSendOtp.classList.remove('hidden');
        messageBox.classList.add('hidden');
        otpInput.value = '';
    });
});