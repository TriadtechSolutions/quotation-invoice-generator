/**
 * Common JavaScript Utilities for Win Spares Document Management System
 */

// Indian currency formatter
function formatIndianCurrency(amount, showSymbol = true, showSlashDash = false) {
    if (amount === null || amount === undefined || isNaN(amount)) {
        amount = 0;
    }
    const num = Math.abs(Number(amount));
    const isNegative = Number(amount) < 0;

    const intPart = Math.floor(num);
    const decimalPart = Math.round((num - intPart) * 100);

    let numStr = intPart.toString();
    let formattedInt = "";

    if (numStr.length <= 3) {
        formattedInt = numStr;
    } else {
        const last3 = numStr.substring(numStr.length - 3);
        let other = numStr.substring(0, numStr.length - 3);
        const parts = [];
        while (other.length > 2) {
            parts.push(other.substring(other.length - 2));
            other = other.substring(0, other.length - 2);
        }
        if (other) parts.push(other);
        parts.reverse();
        formattedInt = parts.join(",") + "," + last3;
    }

    const decStr = decimalPart > 0 ? "." + decimalPart.toString().padStart(2, '0') : "";
    const symbol = showSymbol ? "₹" : "";
    const suffix = showSlashDash ? "/-" : "";
    const prefix = isNegative ? "-" : "";

    return `${prefix}${symbol}${formattedInt}${decStr}${suffix}`;
}

// Simple Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show shadow-sm`;
    toast.role = 'alert';
    toast.innerHTML = `
    <div>${message}</div>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1090';
    document.body.appendChild(container);
    return container;
}
