document.addEventListener('DOMContentLoaded', () => {
    // ============================================================
    // عناصر صفحه
    // ============================================================

    const sendOtpForm = document.getElementById('form-send-otp');
    const verifyOtpForm = document.getElementById('form-verify-otp');

    const identifierInput = document.getElementById('identifier');
    const otpCodeInput = document.getElementById('otp-code');
    const displayMobile = document.getElementById('display-mobile');

    const btnSendOtp = document.getElementById('btn-send-otp');
    const btnVerifyOtp = document.getElementById('btn-verify-otp');
    const btnBack = document.getElementById('btn-back');

    const messageBox = document.getElementById('message-box');

    // نگهداری شناسه ورود (ایمیل یا شماره موبایل) در حافظه موقت
    let currentIdentifier = '';


    // ============================================================
    // 1. بررسی وضعیت ورود قبلی کاربر
    // ============================================================

    if (localStorage.getItem('token')) {
        window.location.href = 'index.html';
        return;
    }


    // ============================================================
    // توابع مدیریت پیام‌ها
    // ============================================================

    function showMessage(message, isError = true) {
        if (!messageBox) return;

        messageBox.textContent = message;
        messageBox.className = `message-box ${isError ? 'error' : 'success'}`;
        messageBox.classList.remove('hidden');
    }

    function hideMessage() {
        if (messageBox) {
            messageBox.classList.add('hidden');
        }
    }


    // ============================================================
    // 2. مدیریت ارسال کد تأیید (مرحله اول)
    // ============================================================

    if (sendOtpForm) {
        sendOtpForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            hideMessage();

            const identifier = identifierInput?.value.trim() || '';

            if (!identifier) {
                showMessage('لطفاً شماره موبایل یا ایمیل خود را وارد کنید.');
                identifierInput?.focus();
                return;
            }

            // غیرفعال کردن دکمه هنگام ارسال درخواست
            if (btnSendOtp) {
                btnSendOtp.disabled = true;
                btnSendOtp.textContent = 'در حال ارسال...';
            }

            try {
                // فراخوانی API ارسال OTP
                const response = await API.auth.sendOtp({ identifier });

                currentIdentifier = identifier;

                if (displayMobile) {
                    displayMobile.textContent = identifier;
                }

                // تغییر فرم‌ها: پنهان کردن فرم ارسال و نمایش فرم ورود کد
                sendOtpForm.classList.add('hidden');
                verifyOtpForm.classList.remove('hidden');

                showMessage(response?.message || 'کد تأیید با موفقیت ارسال شد.', false);

                if (otpCodeInput) {
                    otpCodeInput.focus();
                }

            } catch (error) {
                console.error('Send OTP Error:', error);
                showMessage(error?.message || 'خطا در ارسال کد تأیید. لطفاً مجدداً تلاش کنید.');
            } finally {
                if (btnSendOtp) {
                    btnSendOtp.disabled = false;
                    btnSendOtp.textContent = 'ارسال کد تایید';
                }
            }
        });
    }


    // ============================================================
    // 3. مدیریت تأیید کد OTP (مرحله دوم)
    // ============================================================

    if (verifyOtpForm) {
        verifyOtpForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            hideMessage();

            const otpCode = otpCodeInput?.value.trim() || '';

            if (!otpCode) {
                showMessage('لطفاً کد تأیید را وارد کنید.');
                otpCodeInput?.focus();
                return;
            }

            // غیرفعال کردن دکمه هنگام ارسال درخواست
            if (btnVerifyOtp) {
                btnVerifyOtp.disabled = true;
                btnVerifyOtp.textContent = 'در حال بررسی...';
            }

            try {
                // فراخوانی API بررسی کد OTP
                const response = await API.auth.verifyOtp({
                    identifier: currentIdentifier,
                    code: otpCode
                });

                // حالت اول: کاربر قبلاً ثبت‌نام کرده و توکن دریافت شده است
                if (response?.access_token) {
                    localStorage.setItem('token', response.access_token);
                    localStorage.removeItem('signup_identifier');

                    showMessage(response.message || 'ورود با موفقیت انجام شد. در حال انتقال...', false);

                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1000);
                    return;
                }

                // حالت دوم: کاربر جدید است و باید به صفحه تکمیل ثبت‌نام منتقل شود
                if (response?.is_new_user || response?.requires_signup) {
                    // ذخیره شناسه تأییدشده در LocalStorage برای استفاده در signup.js
                    localStorage.setItem('signup_identifier', currentIdentifier);

                    showMessage('کد تأیید شد. در حال انتقال به صفحه تکمیل ثبت‌نام...', false);

                    setTimeout(() => {
                        window.location.href = 'signup.html';
                    }, 1000);
                    return;
                }

                showMessage(response?.message || 'کد وارد شده صحیح نمی‌باشد.');

            } catch (error) {
                console.error('Verify OTP Error:', error);
                showMessage(error?.message || 'کد تأیید اشتباه است یا منقضی شده است.');
            } finally {
                if (btnVerifyOtp) {
                    btnVerifyOtp.disabled = false;
                    btnVerifyOtp.textContent = 'تایید و ورود';
                }
            }
        });
    }


    // ============================================================
    // 4. دکمه بازگشت / تغییر شماره
    // ============================================================

    if (btnBack) {
        btnBack.addEventListener('click', () => {
            hideMessage();

            if (otpCodeInput) otpCodeInput.value = '';

            verifyOtpForm.classList.add('hidden');
            sendOtpForm.classList.remove('hidden');

            if (identifierInput) {
                identifierInput.focus();
                identifierInput.select();
            }
        });
    }
});