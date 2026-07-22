<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تشریح ۳۰ موجودیت پایگاه داده - سامانه رزرو بلیت ورزشی</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Tahoma', 'Segoe UI', 'Vazir', sans-serif;
            line-height: 1.8;
            background-color: #f8fafc !important; /* اجباری برای جلوگیری از دارک‌مود */
            color: #1e293b !important;
            padding: 30px 15px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: #ffffff !important;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        /* Header Styling */
        .header {
            text-align: center;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 35px;
        }

        .header h1 {
            color: #1e3a8a;
            font-size: 24px;
            margin-bottom: 8px;
        }

        .header p {
            color: #64748b;
            font-size: 14px;
        }

        /* Section Category Headers */
        .category-title {
            background: linear-gradient(135deg, #1e40af, #2563eb);
            color: #ffffff !important;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 17px;
            margin: 35px 0 20px 0;
        }

        /* Entity Card Styling */
        .entity-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-right: 5px solid #3b82f6;
            border-radius: 8px;
            padding: 18px 20px;
            margin-bottom: 18px;
        }

        .entity-title {
            color: #0f172a;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .entity-title code {
            background-color: #eff6ff;
            color: #2563eb;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 14px;
            direction: ltr;
            display: inline-block;
        }

        .desc-box {
            color: #334155;
            margin-bottom: 8px;
            font-size: 14.5px;
        }

        .origin-box {
            color: #475569;
            background-color: #f8fafc;
            padding: 10px 14px;
            border-radius: 6px;
            border: 1px dashed #cbd5e1;
            font-size: 14px;
        }

        .origin-box strong {
            color: #1e293b;
        }

        /* Print Settings for PDF export */
        @media print {
            body {
                background-color: #ffffff !important;
                padding: 0;
            }
            .container {
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }
            .entity-card {
                page-break-inside: avoid;
                border: 1px solid #cbd5e1;
                border-right: 5px solid #2563eb;
            }
            .category-title {
                background: #1e40af !important;
                color: #ffffff !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }
    </style>
</head>
<body>

    <div class="container">
        
        <div class="header">
            <h1>تشریح کامل موجودیت‌های پایگاه داده (فاز اول)</h1>
            <p>پلتفرم جامع رزرو و خرید آنلاین بلیت مسابقات ورزشی - تحلیل ۳۰ جدول پایگاه داده</p>
        </div>

        <!-- بخش اول -->
        <div class="category-title">۱. مدیریت کاربران، دسترسی‌ها و کیف پول</div>

        <div class="entity-card">
            <div class="entity-title">1. <code>ROLES</code> (نقش‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> این جدول سطح دسترسی افراد در سامانه (مانند تماشاگر عادی، کاربر پشتیبانی، مدیر سیستم) را مشخص می‌کند.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> برای رعایت 3NF و جلوگیری از تکرار رشته‌های متنی (مثل کلمه "تماشاگر") در جدول کاربران طراحی شده است تا مدیریت دسترسی‌ها متمرکز باشد.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">2. <code>USERS</code> (کاربران)</div>
            <div class="desc-box"><strong>توضیح:</strong> اطلاعات پایه و احراز هویت تمام کاربران سامانه (نام، ایمیل، شماره تلفن، هش رمز عبور و...) در آن ذخیره می‌شود.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیازمندی اصلی هر سامانه تعاملی برای ثبت‌نام، ورود (Login) و انتساب خریدها و رزروها به افراد.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">3. <code>SUPPORT_USERS</code> (کاربران پشتیبانی)</div>
            <div class="desc-box"><strong>توضیح:</strong> اطلاعات تکمیلی و اختصاصی کادر پشتیبانی (مانند کد پرسنلی) را نگه می‌دارد.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> با رابطه 1:1 به جدول USERS متصل است تا از وجود ستون‌های خالی (NULL) برای کاربران عادی در جدول اصلی جلوگیری شود (ارتقای کیفیت طراحی 3NF).</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">4. <code>WALLETS</code> (کیف پول)</div>
            <div class="desc-box"><strong>توضیح:</strong> موجودی اعتباری حساب هر کاربر را نگهداری می‌کند.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیازمندی پرداخت سریع درون‌برنامه‌ای و تسریع فرآیند استرداد وجه (Refund) در صورت کنسلی بلیت، بدون نیاز به درگاه بانکی مجدد.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">5. <code>WALLET_TRANSACTIONS</code> (تراکنش‌های کیف پول)</div>
            <div class="desc-box"><strong>توضیح:</strong> ریزِ گردش مالی کیف پول (شارژ، برداشت، عودت وجه) را با تاریخ و توضیحات ثبت می‌کند.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیاز به حسابری مالی (Audit Trail)؛ هیچ تغییر موجودی نباید بدون ثبت سند و تراکنش قبلی انجام شود.</div>
        </div>

        <!-- بخش دوم -->
        <div class="category-title">۲. تقسیمات کشوری و مکان‌ها</div>

        <div class="entity-card">
            <div class="entity-title">6. <code>PROVINCES</code> (استان‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> لیست استان‌های کشور.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> ساختار هرمی تقسیمات کشوری برای جلوگیری از خطای تایپی و تکرار نام استان‌ها.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">7. <code>CITIES</code> (شهرها)</div>
            <div class="desc-box"><strong>توضیح:</strong> لیست شهرهای متصل به هر استان.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> فیلتر کردن مسابقات بر اساس شهر، تعیین شهر محل سکونت کاربر و محل قرارگیری ورزشگاه‌ها (رعایت وابستگی کلیدها در 3NF).</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">8. <code>VENUES</code> (ورزشگاه‌ها / سالن‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> اطلاعات مکان‌های برگزاری بازی‌ها (نام استادیوم، آدرس و ظرفیت کل).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیازمندی تعیین محل فیزیکی برگزاری مسابقات و کنترل عدم فروش بلیت مازاد بر ظرفیت سالن.</div>
        </div>

        <!-- بخش سوم -->
        <div class="category-title">۳. ساختار ورزشی، مسابقات و برگزارکنندگان</div>

        <div class="entity-card">
            <div class="entity-title">9. <code>SPORT_TYPES</code> (انواع رشته‌های ورزشی)</div>
            <div class="desc-box"><strong>توضیح:</strong> انواع رشته‌های پشتیبانی‌شده (فوتبال، والیبال، بسکتبال و...).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> انعطاف‌پذیری سامانه برای پشتیبانی از چندین ورزش و اعمال قوانین و ویژگی‌های متفاوت برای هر ورزش.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">10. <code>ORGANIZERS</code> (برگزارکنندگان)</div>
            <div class="desc-box"><strong>توضیح:</strong> نهادها یا شرکت‌های مسئول برگزاری رویدادها (مانند سازمان لیگ، فدراسیون‌ها).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> تفکیک مسئولیت برگزاری بازی‌ها و تعیین سیاست‌های استرداد بلیت مجزا توسط هر برگزارکننده.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">11. <code>TEAMS</code> (تیم‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> اطلاعات تیم‌های ورزشی (نام تیم، شهر و ورزش مرجع).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> تعریف دو طرف مسابقه (تیم میزبان و تیم میهمان) و جستجوی بلیت بر اساس تیم محبوب.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">12. <code>COMPETITIONS</code> (تورنمنت‌ها / لیگ‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> لیگ‌ها و مسابقاتی که بازی‌ها در قالب آن برگزار می‌شوند (مثل لیگ برتر، جام حذفی).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> دسته‌بندی مسابقات بر اساس فصل و نوع تورنمنت جهت سهولت در جستجو و گزارش‌گیری.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">13. <code>MATCHES</code> (مسابقات)</div>
            <div class="desc-box"><strong>توضیح:</strong> هسته اصلی رویدادها که ترکیب "تیم میزبان + تیم میهمان + ورزشگاه + زمان + برگزارکننده" را مشخص می‌کند.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> برطرف کردن رابطه چندبه‌چند بین تیم‌ها، سالن‌ها و زمان برگزاری و فراهم کردن پایه اصلی عرضه بلیت.</div>
        </div>

        <!-- بخش چهارم -->
        <div class="category-title">۴. بلیت‌فروشی، صندلی‌ها و جزئیات اختصاصی (Polymorphism)</div>

        <div class="entity-card">
            <div class="entity-title">14. <code>TICKET_CATEGORIES</code> (دسته‌بندی بلیت‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> بخش‌بندی استادیوم (روبروی جایگاه، جایگاه ویژه، پشت دروازه و...).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> امکان قیمت‌گذاری متفاوت برای بخش‌های مختلف استادیوم.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">15. <code>TICKETS</code> (بلیت‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> بسته‌های بلیت تعریف‌شده برای یک مسابقه (با قیمت مشخص و ظرفیت باقی‌مانده).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> مدیریت موجودی قابل فروش، قیمت‌گذاری و اتصال صندلی‌ها به مسابقه.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">16. <code>SEATS</code> (صندلی‌ها / جایگاه‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> شماره صندلی، ردیف و بخش دقیق فیزیکی/مجازی.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیازمندی سیستم به "رزرو صندلی مشخص" توسط کاربر و جلوگیری از فروش تکراری یک جایگاه.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">17. <code>FACILITIES</code> (امکانات جانبی)</div>
            <div class="desc-box"><strong>توضیح:</strong> لیست امکانات قابل ارائه (پارکینگ، پذیرایی VIP، گیت مجزا).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> جداسازی لیست امکانات جهت جلوگری از تکرار داده‌ها.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">18. <code>TICKET_FACILITIES</code> (امکانات بلیت - جدول واسط)</div>
            <div class="desc-box"><strong>توضیح:</strong> جدول رابط بین TICKETS و FACILITIES.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> شکستن رابطه چندبه‌چند (N:M) بین بلیت‌ها و امکانات جهت رعایت 1NF.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">19. <code>FOOTBALL_DETAILS</code> (جزئیات اختصاصی بلیت فوتبال)</div>
            <div class="desc-box"><strong>توضیح:</strong> شامل فیلدهای خاص فوتبال مانند شماره گیت ورودی، داشتن پارکینگ و خدمات VIP.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> پیاده‌سازی Polymorphism در 3NF؛ برای اینکه ویژگی‌های خاص فوتبال جدول اصلی بلیت را پر از ستون‌های NULL نکند.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">20. <code>VOLLEYBALL_DETAILS</code> (جزئیات اختصاصی بلیت والیبال)</div>
            <div class="desc-box"><strong>توضیح:</strong> شامل ورودی‌های سالن والیبال و خدمات اختصاصی سالنی.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> تفکیک ویژگی‌های مسابقات سالنی والیبال بر اساس اصول نرمال‌سازی.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">21. <code>BASKETBALL_DETAILS</code> (جزئیات اختصاصی بلیت بسکتبال)</div>
            <div class="desc-box"><strong>توضیح:</strong> شامل اطلاعات فودکورت و خدمات اختصاصی بسکتبال.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> تفکیک ویژگی‌های خاص مسابقات بسکتبال بر اساس اصول نرمال‌سازی.</div>
        </div>

        <!-- بخش پنجم -->
        <div class="category-title">۵. فرآیند رزرو و پرداخت</div>

        <div class="entity-card">
            <div class="entity-title">22. <code>RESERVATIONS</code> (رزروها)</div>
            <div class="desc-box"><strong>توضیح:</strong> درخواست اولیه خرید کاربر که شامل تعداد بلیت، مبلغ کل، وضعیت و مهلت زمان رزرو موقت (reserved_until) است.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیازمندی منطقی سیستم برای قفل کردن بلیت به مدت چند دقیقه تا کاربر پرداخت را تکمیل کند.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">23. <code>RESERVED_SEATS</code> (صندلی‌های قفل‌شده)</div>
            <div class="desc-box"><strong>توضیح:</strong> صندلی‌های خاصی که در یک رزرو موقت به کاربر تخصیص داده شده‌اند.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> مدیریت همزمانی (Concurrency Control)؛ جلوی این که دو نفر هم‌زمان یک صندلی مشخص را انتخاب کنند می‌گیرد.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">24. <code>PAYMENTS</code> (پرداخت‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> اطلاعات مالی خرید نهایی (روش پرداخت، کد پیگیری درگاه، زمان و وضعیت).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> ثبت رسمی و قانونی موفقیت/شکست عملیات پرداخت برای تبدیل رزرو موقت به بلیت قطعی.</div>
        </div>

        <!-- بخش ششم -->
        <div class="category-title">۶. کنسلی، قوانین و استرداد وجه</div>

        <div class="entity-card">
            <div class="entity-title">25. <code>CANCELLATION_POLICIES</code> (سیاست‌های کنسلی)</div>
            <div class="desc-box"><strong>توضیح:</strong> عناوین و ساختار کلی قوانین استرداد مربوط به هر برگزارکننده یا رشته ورزشی.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> امکان تعریف قوانین کنسلی متفاوت برای برگزارکنندگان مختلف.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">26. <code>CANCELLATION_POLICY_RULES</code> (قوانین جریمه کنسلی)</div>
            <div class="desc-box"><strong>توضیح:</strong> درصد جریمه بر اساس بازه زمانی (مثلاً: تا ۲۴ ساعت قبل بازی ۱۰٪ جریمه، تا ۶ ساعت قبل ۵۰٪ جریمه).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> محاسبه هوشمند و خودکار میزان جریمه هنگام ثبت درخواست کنسلی.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">27. <code>CANCELLATION_REQUESTS</code> (درخواست‌های کنسلی / تغییر صندلی)</div>
            <div class="desc-box"><strong>توضیح:</strong> درخواست‌های ثبت‌شده توسط تماشاگر برای انصراف از خرید یا جابه‌جایی جایگاه.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> لزوم بررسی و تایید درخواست کنسلی یا جابه‌جایی صندلی توسط کادر پشتیبانی قبل از واریز پول.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">28. <code>REFUNDS</code> (استرداد وجه)</div>
            <div class="desc-box"><strong>توضیح:</strong> ثبت سند عودت پول به کاربر پس از موافقت با درخواست کنسلی.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> شفافیت مالی و متصل کردن درخواست کنسلی تاییدشده به تراکنش کیف پول/بانکی.</div>
        </div>

        <!-- بخش هفتم -->
        <div class="category-title">۷. پشتیبانی و گزارش‌دهی</div>

        <div class="entity-card">
            <div class="entity-title">29. <code>REPORT_CATEGORIES</code> (دسته‌بندی گزارش‌ها)</div>
            <div class="desc-box"><strong>توضیح:</strong> موضوعات شکایات و گزارش‌ها (تخلف در استادیوم، مشکل فنی بلیت، کیفیت نامناسب جایگاه و...).</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> دسته بندی گزارش‌ها برای ارجاع سریع به بخش مربوطه.</div>
        </div>

        <div class="entity-card">
            <div class="entity-title">30. <code>REPORTS</code> (گزارش‌ها و شکایات)</div>
            <div class="desc-box"><strong>توضیح:</strong> متون شکایات یا گزارش‌های ثبت‌شده توسط تماشاگران به همراه پاسخ پشتیبان.</div>
            <div class="origin-box"><strong>منشأ و دلیل وجود:</strong> نیازمندی سیستم برای دریافت نظرات، رسیدگی به مشکلات تماشاگران و نظارت بر کیفیت خدمات.</div>
        </div>

    </div>

</body>
</html>