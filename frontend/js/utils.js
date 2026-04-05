// 數字格式化工具

function fmtNum(n, decimals = 2) {
  if (n == null || isNaN(n)) return "—";
  return Number(n).toLocaleString("zh-TW", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtPct(n) {
  if (n == null || isNaN(n)) return "—";
  const sign = n >= 0 ? "+" : "";
  return `${sign}${fmtNum(n, 2)}%`;
}

function fmtMoney(n) {
  if (n == null || isNaN(n)) return "—";
  return `$${fmtNum(n, 0)}`;
}

function pctClass(n) {
  if (n > 0) return "value-green";
  if (n < 0) return "value-red";
  return "";
}

// Toast 通知
function showToast(msg, type = "info", duration = 3000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// Loading state helpers
function setLoading(btn, loading) {
  if (loading) {
    btn.disabled = true;
    btn._origText = btn.textContent;
    btn.innerHTML = `<span class="spinner"></span>${btn._origText}`;
  } else {
    btn.disabled = false;
    btn.textContent = btn._origText || btn.textContent;
  }
}
