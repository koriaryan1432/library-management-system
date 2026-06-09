/* ════════════════════════════════════════════
   BIBLIOTHECA — Frontend Logic
   ════════════════════════════════════════════ */

const API = '';   // Same origin; change to 'http://localhost:5000' if separate

// ─── Navigation ──────────────────────────────

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    const page = btn.dataset.page;
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`page-${page}`).classList.add('active');
    // Refresh data on navigation
    if (page === 'dashboard') { loadStats(); loadDashboardLoans(); }
    if (page === 'books')     { loadBooks(); }
    if (page === 'members')   { loadMembers(); }
    if (page === 'loans')     { loadLoans(); }
    if (page === 'issue')     { loadIssueSelects(); }
  });
});

// ─── Toast ───────────────────────────────────

function toast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type === 'error' ? 'error' : ''} show`;
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ─── Modal ───────────────────────────────────

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
});

// ─── API Helper ──────────────────────────────

async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  return res.json();
}

// ─── Formatters ──────────────────────────────

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function statusBadge(s) {
  const map = { active: 'badge-active', returned: 'badge-returned', overdue: 'badge-overdue' };
  return `<span class="badge ${map[s] || ''}">${s}</span>`;
}

// ════════════════════════════════════════════
// DASHBOARD
// ════════════════════════════════════════════

async function loadStats() {
  const s = await api('/api/stats');
  document.getElementById('stat-books').textContent   = s.total_books;
  document.getElementById('stat-members').textContent = s.total_members;
  document.getElementById('stat-loans').textContent   = s.active_loans;
  document.getElementById('stat-overdue').textContent = s.overdue_loans;
}

async function loadDashboardLoans() {
  const loans = await api('/api/loans');
  const tbody = document.getElementById('dashboard-loans-body');
  const recent = loans.slice(0, 10);
  if (!recent.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No loan records yet.</td></tr>';
    return;
  }
  tbody.innerHTML = recent.map(l => `
    <tr>
      <td><strong>${esc(l.book_title)}</strong></td>
      <td>${esc(l.member_name)}</td>
      <td>${fmtDate(l.loaned_at)}</td>
      <td>${fmtDate(l.due_at)}</td>
      <td>${statusBadge(l.status)}</td>
    </tr>
  `).join('');
}

// ════════════════════════════════════════════
// BOOKS
// ════════════════════════════════════════════

async function loadBooks() {
  const search = document.getElementById('books-search').value;
  const books = await api(`/api/books?search=${encodeURIComponent(search)}`);
  const tbody = document.getElementById('books-body');
  if (!books.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No books found.</td></tr>';
    return;
  }
  tbody.innerHTML = books.map(b => `
    <tr>
      <td><strong>${esc(b.title)}</strong></td>
      <td>${esc(b.author)}</td>
      <td>${esc(b.genre || '—')}</td>
      <td style="font-size:0.78rem;color:var(--text-dim)">${esc(b.isbn || '—')}</td>
      <td>${b.total_copies}</td>
      <td class="${b.available > 0 ? 'avail-yes' : 'avail-no'}">${b.available}</td>
      <td>
        <div class="action-cell">
          <button class="btn btn-ghost btn-sm" onclick="editBook(${b.id},'${esc(b.title)}','${esc(b.author)}','${esc(b.isbn||'')}','${esc(b.genre||'')}',${b.total_copies})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="deleteBook(${b.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join('');
}

let editingBookId = null;

function editBook(id, title, author, isbn, genre, copies) {
  editingBookId = id;
  document.getElementById('book-title').value  = title;
  document.getElementById('book-author').value = author;
  document.getElementById('book-isbn').value   = isbn;
  document.getElementById('book-genre').value  = genre;
  document.getElementById('book-copies').value = copies;
  openModal('modal-add-book');
}

async function saveBook() {
  const data = {
    title:        document.getElementById('book-title').value.trim(),
    author:       document.getElementById('book-author').value.trim(),
    isbn:         document.getElementById('book-isbn').value.trim(),
    genre:        document.getElementById('book-genre').value.trim(),
    total_copies: parseInt(document.getElementById('book-copies').value),
  };
  if (!data.title || !data.author) { toast('Title and Author are required', 'error'); return; }

  let res;
  if (editingBookId) {
    res = await api(`/api/books/${editingBookId}`, 'PUT', data);
  } else {
    res = await api('/api/books', 'POST', data);
  }

  if (res.error) { toast(res.error, 'error'); return; }
  toast(res.message);
  closeModal('modal-add-book');
  editingBookId = null;
  ['book-title','book-author','book-isbn','book-genre'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('book-copies').value = 1;
  loadBooks();
}

async function deleteBook(id) {
  if (!confirm('Delete this book?')) return;
  const res = await api(`/api/books/${id}`, 'DELETE');
  if (res.error) { toast(res.error, 'error'); return; }
  toast('Book deleted');
  loadBooks();
}

// ════════════════════════════════════════════
// MEMBERS
// ════════════════════════════════════════════

async function loadMembers() {
  const search = document.getElementById('members-search').value;
  const members = await api(`/api/members?search=${encodeURIComponent(search)}`);
  const tbody = document.getElementById('members-body');
  if (!members.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No members found.</td></tr>';
    return;
  }
  tbody.innerHTML = members.map(m => `
    <tr>
      <td><strong>${esc(m.name)}</strong></td>
      <td>${esc(m.email)}</td>
      <td>${esc(m.phone || '—')}</td>
      <td>${fmtDate(m.joined_at)}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deleteMember(${m.id})">Remove</button>
      </td>
    </tr>
  `).join('');
}

async function saveMember() {
  const data = {
    name:  document.getElementById('member-name').value.trim(),
    email: document.getElementById('member-email').value.trim(),
    phone: document.getElementById('member-phone').value.trim(),
  };
  if (!data.name || !data.email) { toast('Name and Email are required', 'error'); return; }
  const res = await api('/api/members', 'POST', data);
  if (res.error) { toast(res.error, 'error'); return; }
  toast('Member added successfully');
  closeModal('modal-add-member');
  ['member-name','member-email','member-phone'].forEach(id => document.getElementById(id).value = '');
  loadMembers();
}

async function deleteMember(id) {
  if (!confirm('Remove this member?')) return;
  const res = await api(`/api/members/${id}`, 'DELETE');
  toast(res.message || 'Removed');
  loadMembers();
}

// ════════════════════════════════════════════
// LOANS
// ════════════════════════════════════════════

let loanStatusFilter = '';

function setLoanFilter(btn, status) {
  document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loanStatusFilter = status;
  loadLoans();
}

async function loadLoans() {
  const loans = await api(`/api/loans?status=${loanStatusFilter}`);
  const tbody = document.getElementById('loans-body');
  if (!loans.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No records found.</td></tr>';
    return;
  }
  tbody.innerHTML = loans.map(l => `
    <tr>
      <td><strong>${esc(l.book_title)}</strong></td>
      <td style="color:var(--text-dim)">${esc(l.author)}</td>
      <td>${esc(l.member_name)}</td>
      <td>${fmtDate(l.loaned_at)}</td>
      <td>${fmtDate(l.due_at)}</td>
      <td>${fmtDate(l.returned_at)}</td>
      <td>${statusBadge(l.status)}</td>
      <td>
        ${l.status === 'active' || l.status === 'overdue'
          ? `<button class="btn btn-ghost btn-sm" onclick="returnBook(${l.id})">Return</button>`
          : '<span style="color:var(--text-dim);font-size:0.78rem">—</span>'}
      </td>
    </tr>
  `).join('');
}

async function returnBook(loanId) {
  if (!confirm('Mark this book as returned?')) return;
  const res = await api(`/api/loans/${loanId}/return`, 'PUT');
  toast(res.message);
  loadLoans();
  loadStats();
}

// ════════════════════════════════════════════
// ISSUE BOOK
// ════════════════════════════════════════════

async function loadIssueSelects() {
  const [books, members] = await Promise.all([
    api('/api/books'),
    api('/api/members'),
  ]);

  const bSel = document.getElementById('issue-book');
  const mSel = document.getElementById('issue-member');

  bSel.innerHTML = books
    .filter(b => b.available > 0)
    .map(b => `<option value="${b.id}">${esc(b.title)} — ${esc(b.author)} (${b.available} avail.)</option>`)
    .join('');

  if (!bSel.options.length) bSel.innerHTML = '<option disabled>No books available</option>';

  mSel.innerHTML = members
    .map(m => `<option value="${m.id}">${esc(m.name)} (${esc(m.email)})</option>`)
    .join('');

  if (!mSel.options.length) mSel.innerHTML = '<option disabled>No members registered</option>';
}

async function issueLoan() {
  const book_id   = document.getElementById('issue-book').value;
  const member_id = document.getElementById('issue-member').value;
  const days      = document.getElementById('issue-days').value;

  if (!book_id || !member_id) { toast('Please select a book and a member', 'error'); return; }

  const res = await api('/api/loans', 'POST', { book_id, member_id, days });
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`Book issued! Due: ${fmtDate(res.due_at)}`);
  loadIssueSelects();
}

// ─── XSS protection ──────────────────────────
function esc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ─── Initialise ──────────────────────────────
loadStats();
loadDashboardLoans();
