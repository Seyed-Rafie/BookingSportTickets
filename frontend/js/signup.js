document.addEventListener('DOMContentLoaded', () => {
    // ============================================================
    // عناصر صفحه
    // ============================================================

    const signupForm = document.getElementById('form-signup');

    const firstNameInput = document.getElementById('first-name');
    const lastNameInput = document.getElementById('last-name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');

    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');

    const roleSelect = document.getElementById('role-id');

    const submitBtn = document.getElementById('btn-signup');
    const messageBox = document.getElementById('message-box');


    // ============================================================
    // ۱. اگر کاربر قبلاً وارد شده، اجازه ورود به Signup نداریم
    // ============================================================

    if (localStorage.getItem('token')) {
        window.location.href = 'index.html';
        return;
    }


    // ============================================================
    // تابع نمایش پیام
    // ============================================================

    function showMessage(message, isError = true) {
        if (!messageBox) return;

        messageBox.textContent = message;
        messageBox.className = `message-box ${isError ? 'error' : 'success'}`;
        messageBox.classList.remove('hidden');
    }


    // ============================================================
    // ۲. دریافت شناسه تأییدشده از مرحله OTP
    // ============================================================

    const signupIdentifier = localStorage.getItem('signup_identifier');

    if (!signupIdentifier) {
        showMessage(
            'اطلاعات ثبت‌نام یافت نشد. لطفاً ابتدا شماره موبایل یا ایمیل خود را تأیید کنید.'
        );

        if (signupForm) {
            signupForm.classList.add('hidden');
        }

        return;
    }


    // ============================================================
    // ۳. تشخیص نوع شناسه (ایمیل یا شماره تلفن) و جای‌گذاری هوشمند
    // ============================================================

    const isEmailIdentifier = signupIdentifier.includes('@');

    if (isEmailIdentifier) {
        // کاربر با ایمیل وارد شده است
        if (emailInput) {
            emailInput.value = signupIdentifier;
            emailInput.readOnly = true; // قفل کردن فیلد ایمیل
        }
        if (phoneInput) {
            phoneInput.value = '';
            phoneInput.readOnly = false; // باز گذاشتن فیلد تلفن برای ورود کاربر
        }
    } else {
        // کاربر با شماره تلفن وارد شده است
        if (phoneInput) {
            phoneInput.value = signupIdentifier;
            phoneInput.readOnly = true; // قفل کردن فیلد تلفن
        }
        if (emailInput) {
            emailInput.value = '';
            emailInput.readOnly = false; // باز گذاشتن فیلد ایمیل برای ورود کاربر
        }
    }


    // ============================================================
    // ۴. مدیریت ارسال فرم
    // ============================================================

    if (!signupForm) {
        console.error('Signup form not found.');
        return;
    }


    signupForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        // --------------------------------------------------------
        // دریافت مقادیر فرم
        // --------------------------------------------------------

        const firstName = firstNameInput?.value.trim() || '';
        const lastName = lastNameInput?.value.trim() || '';

        // استخراج هماهنگ مقادیر بر اساس نوع ورود
        const email = isEmailIdentifier 
            ? signupIdentifier 
            : (emailInput?.value.trim() || null);

        const phone = isEmailIdentifier 
            ? (phoneInput?.value.trim() || null) 
            : signupIdentifier;

        const password = passwordInput?.value || '';
        const confirmPassword = confirmPasswordInput?.value || '';

        const roleId = roleSelect ? parseInt(roleSelect.value, 10) : 2;


        // ========================================================
        // اعتبارسنجی
        // ========================================================

        if (!firstName) {
            showMessage('لطفاً نام خود را وارد کنید.');
            firstNameInput?.focus();
            return;
        }

        if (!lastName) {
            showMessage('لطفاً نام خانوادگی خود را وارد کنید.');
            lastNameInput?.focus();
            return;
        }

        if (!email && !phone) {
            showMessage('وارد کردن ایمیل یا شماره موبایل الزامی است.');
            return;
        }

        if (!password) {
            showMessage('لطفاً رمز عبور را وارد کنید.');
            passwordInput?.focus();
            return;
        }

        if (password.length < 6) {
            showMessage('رمز عبور باید حداقل ۶ کاراکتر باشد.');
            passwordInput?.focus();
            return;
        }

        if (password !== confirmPassword) {
            showMessage('رمز عبور و تکرار آن یکسان نیستند.');
            confirmPasswordInput?.focus();
            return;
        }

        if (!Number.isInteger(roleId)) {
            showMessage('نقش کاربر نامعتبر است.');
            return;
        }


        // ========================================================
        // ۵. جلوگیری از ارسال چندباره
        // ========================================================

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'در حال ثبت‌نام...';
        }


        // ========================================================
        // ۶. ساخت Payload
        // ========================================================

        const signupPayload = {
            first_name: firstName,
            last_name: lastName,
            email: email,
            phone: phone,
            password: password,
            role_id: roleId
        };

        console.log('Signup payload:', {
            ...signupPayload,
            password: '********'
        });


        // ========================================================
        // ۷. ارسال درخواست به Backend
        // ========================================================

        try {
            const response = await API.auth.signup(signupPayload);

            if (response?.access_token) {
                // ذخیره JWT
                localStorage.setItem('token', response.access_token);

                // حذف identifier موقت
                localStorage.removeItem('signup_identifier');

                showMessage(
                    response.message || 'ثبت‌نام با موفقیت انجام شد. در حال انتقال...',
                    false
                );

                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1000);

                return;
            }

            showMessage(
                response?.message || 'ثبت‌نام انجام شد اما توکن ورود دریافت نشد.'
            );

        } catch (error) {
            console.error('Signup Error:', error);
            showMessage(
                error?.message || 'خطا در انجام ثبت‌نام. لطفاً مجدداً تلاش کنید.'
            );
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'تکمیل ثبت‌نام';
            }
        }
    });
});