/**
 * Interactive Quotation Form Handler
 * Live calculations, dynamic items, customer autocomplete, scope item reordering.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCustomerAutocomplete();
    initItemsTable();
    initScopeManager();
    calculateAll();
});

/* -------------------------------------------------------------
 * 1. LIVE CALCULATIONS & ITEM ROWS
 * ------------------------------------------------------------- */
function initItemsTable() {
    const tableBody = document.getElementById('items-table-body');
    const addRowBtn = document.getElementById('add-item-btn');

    if (addRowBtn) {
        addRowBtn.addEventListener('click', () => {
            addItemRow();
        });
    }

    if (tableBody) {
        tableBody.addEventListener('input', (e) => {
            if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-rate')) {
                calculateRow(e.target.closest('tr'));
                calculateAll();
            }
        });

        tableBody.addEventListener('click', (e) => {
            if (e.target.closest('.delete-item-btn')) {
                const row = e.target.closest('tr');
                if (tableBody.querySelectorAll('tr').length > 1) {
                    row.remove();
                    calculateAll();
                    reindexItems();
                } else {
                    showToast('Quotation must contain at least one item.', 'warning');
                }
            }
        });
    }

    // Tax rate inputs
    const sgstInput = document.getElementById('sgstRate');
    const cgstInput = document.getElementById('cgstRate');
    if (sgstInput) sgstInput.addEventListener('input', calculateAll);
    if (cgstInput) cgstInput.addEventListener('input', calculateAll);
}

function addItemRow(itemData = { item: '', qty: 1, rate: 0, amount: 0 }) {
    const tableBody = document.getElementById('items-table-body');
    if (!tableBody) return;

    const rowCount = tableBody.querySelectorAll('tr').length;
    const tr = document.createElement('tr');
    tr.className = 'item-row';

    tr.innerHTML = `
    <td>
      <input type="text" name="items[${rowCount}][item]" class="form-control item-name" 
             placeholder="e.g. VRF Full Service" value="${itemData.item || ''}" required>
    </td>
    <td style="width: 140px;">
      <input type="number" step="any" min="0.01" name="items[${rowCount}][qty]" class="form-control item-qty" 
             value="${itemData.qty || 1}" required>
    </td>
    <td style="width: 160px;">
      <div class="input-group">
        <span class="input-group-text">₹</span>
        <input type="number" step="any" min="0" name="items[${rowCount}][rate]" class="form-control item-rate" 
               placeholder="2500" value="${itemData.rate || ''}" required>
      </div>
    </td>
    <td style="width: 180px;">
      <input type="text" class="form-control item-amount-display" readonly value="${formatIndianCurrency(itemData.amount || 0, true, true)}">
      <input type="hidden" name="items[${rowCount}][amount]" class="item-amount-val" value="${itemData.amount || 0}">
    </td>
    <td class="text-center" style="width: 60px;">
      <button type="button" class="btn btn-outline-danger btn-sm delete-item-btn" title="Remove item">
        <i class="bi bi-trash"></i> &times;
      </button>
    </td>
  `;

    tableBody.appendChild(tr);
    calculateRow(tr);
    calculateAll();
}

function calculateRow(tr) {
    const qtyInput = tr.querySelector('.item-qty');
    const rateInput = tr.querySelector('.item-rate');
    const amountDisplay = tr.querySelector('.item-amount-display');
    const amountHidden = tr.querySelector('.item-amount-val');

    const qty = parseFloat(qtyInput.value) || 0;
    const rate = parseFloat(rateInput.value) || 0;
    const amount = Math.max(0, qty * rate);

    amountDisplay.value = formatIndianCurrency(amount, true, true);
    amountHidden.value = amount;
}

function reindexItems() {
    const rows = document.querySelectorAll('#items-table-body tr');
    rows.forEach((tr, index) => {
        tr.querySelector('.item-name').name = `items[${index}][item]`;
        tr.querySelector('.item-qty').name = `items[${index}][qty]`;
        tr.querySelector('.item-rate').name = `items[${index}][rate]`;
        tr.querySelector('.item-amount-val').name = `items[${index}][amount]`;
    });
}

function calculateAll() {
    const rows = document.querySelectorAll('#items-table-body tr');
    let subtotal = 0;

    rows.forEach(tr => {
        const qty = parseFloat(tr.querySelector('.item-qty').value) || 0;
        const rate = parseFloat(tr.querySelector('.item-rate').value) || 0;
        subtotal += Math.max(0, qty * rate);
    });

    const sgstRate = parseFloat(document.getElementById('sgstRate')?.value) || 9.0;
    const cgstRate = parseFloat(document.getElementById('cgstRate')?.value) || 9.0;

    const sgstAmount = (subtotal * sgstRate) / 100;
    const cgstAmount = (subtotal * cgstRate) / 100;
    const grandTotal = subtotal + sgstAmount + cgstAmount;

    // Update summary UI
    const subtotalEl = document.getElementById('summary-subtotal');
    const sgstEl = document.getElementById('summary-sgst');
    const cgstEl = document.getElementById('summary-cgst');
    const grandTotalEl = document.getElementById('summary-grand-total');

    if (subtotalEl) subtotalEl.textContent = formatIndianCurrency(subtotal, true, true);
    if (sgstEl) sgstEl.textContent = formatIndianCurrency(sgstAmount, true, true);
    if (cgstEl) cgstEl.textContent = formatIndianCurrency(cgstAmount, true, true);
    if (grandTotalEl) grandTotalEl.textContent = formatIndianCurrency(grandTotal, true, true);
}

/* -------------------------------------------------------------
 * 2. CUSTOMER AUTOCOMPLETE & SELECTION
 * ------------------------------------------------------------- */
function initCustomerAutocomplete() {
    const nameInput = document.getElementById('customer-name');
    const suggestionsBox = document.getElementById('customer-suggestions');
    if (!nameInput || !suggestionsBox) return;

    nameInput.addEventListener('input', async (e) => {
        const val = e.target.value.trim();
        if (val.length < 1) {
            suggestionsBox.innerHTML = '';
            suggestionsBox.style.display = 'none';
            return;
        }

        try {
            const res = await fetch(`/api/customers?q=${encodeURIComponent(val)}`);
            const customers = await res.json();

            if (customers.length > 0) {
                suggestionsBox.innerHTML = customers.map(c => `
          <div class="suggestion-item" data-name="${escapeHtml(c.name)}" data-address="${escapeHtml(c.address || '')}">
            <strong>${escapeHtml(c.name)}</strong>
            ${c.address ? `<div class="small text-muted text-truncate">${escapeHtml(c.address)}</div>` : ''}
          </div>
        `).join('');
                suggestionsBox.style.display = 'block';
            } else {
                suggestionsBox.innerHTML = '';
                suggestionsBox.style.display = 'none';
            }
        } catch (err) {
            console.error('Customer fetch error:', err);
        }
    });

    suggestionsBox.addEventListener('click', (e) => {
        const item = e.target.closest('.suggestion-item');
        if (item) {
            nameInput.value = item.dataset.name;
            const addrInput = document.getElementById('customer-address');
            if (addrInput) addrInput.value = item.dataset.address;
            suggestionsBox.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (!nameInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
}

function escapeHtml(str) {
    return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* -------------------------------------------------------------
 * 3. SCOPE OF SERVICE MANAGER
 * ------------------------------------------------------------- */
function initScopeManager() {
    const scopeContainer = document.getElementById('scope-items-container');
    const addScopeBtn = document.getElementById('add-scope-btn');

    if (addScopeBtn) {
        addScopeBtn.addEventListener('click', () => {
            addScopeItem();
        });
    }

    if (scopeContainer) {
        scopeContainer.addEventListener('click', (e) => {
            const itemRow = e.target.closest('.scope-item-row');
            if (!itemRow) return;

            if (e.target.closest('.delete-scope-btn')) {
                if (scopeContainer.querySelectorAll('.scope-item-row').length > 1) {
                    itemRow.remove();
                    reindexScope();
                } else {
                    showToast('At least one scope item is required.', 'warning');
                }
            } else if (e.target.closest('.move-up-btn')) {
                const prev = itemRow.previousElementSibling;
                if (prev) {
                    scopeContainer.insertBefore(itemRow, prev);
                    reindexScope();
                }
            } else if (e.target.closest('.move-down-btn')) {
                const next = itemRow.nextElementSibling;
                if (next) {
                    scopeContainer.insertBefore(next, itemRow);
                    reindexScope();
                }
            }
        });
    }
}

function addScopeItem(text = '') {
    const scopeContainer = document.getElementById('scope-items-container');
    if (!scopeContainer) return;

    const index = scopeContainer.querySelectorAll('.scope-item-row').length;
    const div = document.createElement('div');
    div.className = 'scope-item-row mb-2 d-flex align-items-center gap-2';

    div.innerHTML = `
    <span class="badge bg-secondary scope-num">${index + 1}</span>
    <input type="text" name="scope[]" class="form-control scope-input" value="${escapeHtml(text)}" 
           placeholder="Enter scope detail e.g. Preventive maintenance report" required>
    <div class="btn-group btn-group-sm">
      <button type="button" class="btn btn-outline-secondary move-up-btn" title="Move Up">&uarr;</button>
      <button type="button" class="btn btn-outline-secondary move-down-btn" title="Move Down">&darr;</button>
      <button type="button" class="btn btn-outline-danger delete-scope-btn" title="Delete">&times;</button>
    </div>
  `;

    scopeContainer.appendChild(div);
    reindexScope();
}

function reindexScope() {
    const rows = document.querySelectorAll('#scope-items-container .scope-item-row');
    rows.forEach((row, idx) => {
        row.querySelector('.scope-num').textContent = idx + 1;
    });
}
