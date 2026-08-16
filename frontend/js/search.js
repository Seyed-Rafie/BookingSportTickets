import API from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const ticketsContainer = document.getElementById('tickets-container');
    const ticketModal = document.getElementById('ticket-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const reserveBtn = document.getElementById('reserve-btn');

    let currentSelectedTicketId = null;

    async function loadTickets(filters = {}) {
        ticketsContainer.innerHTML = '<p style="text-align:center; width:100%;">در حال جستجوی مسابقات...</p>';
        try {
            const tickets = await API.tickets.search(filters);
            
            if (!tickets || tickets.length === 0) {
                ticketsContainer.innerHTML = '<p style="text-align:center; width:100%;">هیچ مسابقه‌ای با این مشخصات یافت نشد.</p>';
                return;
            }

            ticketsContainer.innerHTML = '';
            
            tickets.forEach(ticket => {
                const card = document.createElement('div');
                card.className = 'ticket-card';
                card.innerHTML = `
                    <h3>${ticket.match.home_team.name} - ${ticket.match.away_team.name}</h3>
                    <p><strong>ورزش:</strong> ${ticket.match.sport_type_name}</p>
                    <p><strong>ورزشگاه:</strong> ${ticket.match.venue_name} (${ticket.match.city_name || 'نامشخص'})</p>
                    <p><strong>تاریخ:</strong> ${new Date(ticket.match.match_datetime).toLocaleString('fa-IR')}</p>
                    <p><strong>شروع قیمت از:</strong> ${Number(ticket.price).toLocaleString('fa-IR')} تومان</p>

                    <div class="ticket-actions">
                        <button class="btn btn-primary view-details-btn" data-id="${ticket.ticket_id}">مشاهده و رزرو</button>
                    </div>
                `;
                ticketsContainer.appendChild(card);
            });

            document.querySelectorAll('.view-details-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    openTicketDetails(e.target.getAttribute('data-id'));
                });
            });

        } catch (error) {
            ticketsContainer.innerHTML = `<p style="color:var(--danger); text-align:center; width:100%;">خطا: ${error.message}</p>`;
        }
    }

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const filters = {
            q: document.getElementById('query').value,
            sport_type_id: document.getElementById('sport-type').value,
            city_id: document.getElementById('city').value,
            min_price: document.getElementById('min-price').value,
            max_price: document.getElementById('max-price').value,
            date_from: document.getElementById('date-from').value,
            date_to: document.getElementById('date-to').value
        };
        
        loadTickets(filters);
    });

    async function openTicketDetails(ticketId) {
        modalTitle.innerText = "در حال بارگذاری...";
        modalBody.innerHTML = "";
        ticketModal.classList.add('active');
        currentSelectedTicketId = ticketId;

        try {
            const ticketDetail = await API.tickets.getDetails(ticketId);
            
            modalTitle.innerText = `${ticketDetail.match.home_team.name} - ${ticketDetail.match.away_team.name}`;
            modalBody.innerHTML = `
                <p><strong>ورزش:</strong> ${ticketDetail.match.sport_type_name}</p>
                <p><strong>ورزشگاه:</strong> ${ticketDetail.match.venue_name}</p>
                <p><strong>زمان:</strong> ${new Date(ticketDetail.match.match_datetime).toLocaleString('fa-IR')}</p>
                <p><strong>قیمت:</strong> ${Number(ticketDetail.price).toLocaleString('fa-IR')} تومان</p>
                <p><strong>ظرفیت باقیمانده:</strong> ${ticketDetail.remaining_capacity} صندلی</p>
                
                <div class="form-group" style="margin-top: 1.5rem; border-top: 1px dashed #ccc; padding-top: 1rem;">
                    <label for="seat-input"><strong>انتخاب صندلی (آزمایشی):</strong></label>
                    <input type="text" id="seat-input" class="form-control" placeholder="شناسه صندلی را وارد کنید (مثال: 12)">
                    <small style="color: #666; display:block; margin-top:0.5rem;">* در نسخه نهایی، این بخش تبدیل به نقشه گرافیکی انتخاب صندلی خواهد شد.</small>
                </div>
            `;
            reserveBtn.style.display = ticketDetail.remaining_capacity > 0 ? 'inline-block' : 'none';

        } catch (error) {
            modalTitle.innerText = "خطا";
            modalBody.innerHTML = `<p style="color:var(--danger);">${error.message}</p>`;
            reserveBtn.style.display = 'none';
        }
    }

    closeModalBtn.addEventListener('click', () => ticketModal.classList.remove('active'));

    reserveBtn.addEventListener('click', async () => {
        if (!API.getToken()) {
            alert('برای رزرو بلیط ابتدا باید وارد سایت شوید.');
            window.location.href = 'login.html';
            return;
        }

        // گرفتن شناسه صندلی از فیلد آزمایشی
        const seatInput = document.getElementById('seat-input');
        const seatValue = seatInput ? seatInput.value.trim() : '';

        if (!seatValue) {
            alert('لطفاً حداقل یک شناسه صندلی وارد کنید.');
            return;
        }

        // تبدیل رشته وارد شده به آرایه عددی
        const seatIds = seatValue.split(',').map(s => parseInt(s.trim())).filter(s => !isNaN(s));

        if (seatIds.length === 0) {
            alert('فرمت شناسه صندلی نامعتبر است.');
            return;
        }

        // غیرفعال کردن دکمه برای جلوگیری از کلیک چندباره
        reserveBtn.disabled = true;
        reserveBtn.textContent = 'در حال ثبت رزرو موقت...';

        try {
            // فراخوانی متد create با ticketId و لیست seatIds
            const res = await API.reservations.create(currentSelectedTicketId, seatIds);

            // هدایت به صفحه درگاه پرداخت
            window.location.href = `checkout.html?reservation_id=${res.reservation_id}`;

        } catch (error) {
            alert(`خطا در رزرو: ${error.message}`);
            reserveBtn.disabled = false;
            reserveBtn.textContent = 'ثبت رزرو موقت (۱۰ دقیقه)';
        }
    });

    // لود اولیه مسابقات
    loadTickets();
});