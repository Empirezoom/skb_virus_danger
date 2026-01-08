// Hamburger menu logic
const hamburger = document.getElementById("hamburger");
const mobileNav = document.getElementById("mobileNav");
hamburger.addEventListener("click", () => {
  hamburger.classList.toggle("open");
  mobileNav.classList.toggle("show");
});
hamburger.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    hamburger.click();
  }
});
Array.from(mobileNav.querySelectorAll("a")).forEach((link) => {
  link.addEventListener("click", () => {
    hamburger.classList.remove("open");
    mobileNav.classList.remove("show");
  });
});

// Use Django data - no demo data fallback
let accounts = [];
let paymentHistory = [];
let scheduledPayments = [];
let savedRecipients = [];

// Initialize data after page load
function initializeData() {
  console.log("initializeData called");
  console.log("djangoData:", djangoData);
  if (typeof djangoData !== "undefined" && djangoData.user.is_authenticated) {
    console.log("User authenticated, parsing data");
    // Use real Django data - parse JSON strings
    accounts =
      typeof djangoData.accounts === "string"
        ? JSON.parse(djangoData.accounts)
        : djangoData.accounts || [];
    console.log("accounts:", accounts);
    paymentHistory =
      typeof djangoData.payments === "string"
        ? JSON.parse(djangoData.payments)
        : djangoData.payments || [];
    scheduledPayments =
      typeof djangoData.scheduledPayments === "string"
        ? JSON.parse(djangoData.scheduledPayments)
        : djangoData.scheduledPayments || [];
    savedRecipients = djangoData.recipients
      ? (typeof djangoData.recipients === "string"
          ? JSON.parse(djangoData.recipients)
          : djangoData.recipients
        ).map((r) => r.name)
      : [];
  } else {
    console.log("User not authenticated or djangoData undefined");
    // No demo data - redirect to login if not authenticated
    if (
      typeof djangoData !== "undefined" &&
      !djangoData.user.is_authenticated
    ) {
      window.location.href = "/login/";
    }
  }
}

// Helper function to get CSRF token
function getCSRFToken() {
  if (typeof djangoData !== "undefined" && djangoData.csrfToken) {
    return djangoData.csrfToken;
  }
  // Fallback: try to get from cookie
  const cookieValue = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1];
  return cookieValue || "";
}

// Helper function to make API calls
async function apiCall(endpoint, options = {}) {
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  // Add CSRF token for non-GET requests
  if (options.method && options.method !== "GET") {
    const csrfToken = getCSRFToken();
    if (csrfToken) {
      defaultOptions.headers["X-CSRFToken"] = csrfToken;
    }
  }

  const response = await fetch(endpoint, { ...defaultOptions, ...options });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "API call failed");
  }
  return response.json();
}

// Load data from Django APIs
async function loadData() {
  if (typeof djangoData === "undefined" || !djangoData.user.is_authenticated) {
    return; // No data to load if not authenticated
  }

  // If we already have data from Django template, don't reload from API
  if (accounts.length > 0 || paymentHistory.length > 0) {
    return;
  }

  try {
    // Load accounts
    const accountsData = await apiCall("/api/accounts/");
    accounts = accountsData.accounts;

    // Load payments
    const paymentsData = await apiCall("/api/payments/");
    paymentHistory = paymentsData.payments;
    scheduledPayments = paymentsData.scheduled_payments;

    // Update saved recipients from Django data
    if (djangoData.recipients) {
      savedRecipients = djangoData.recipients.map((r) => r.name);
    }

    // Refresh UI
    populateAccountDropdowns();
    renderSavedRecipients();
    renderPaymentHistory();
    renderScheduledPayments();
    setTimeout(renderAnalytics, 100);
  } catch (error) {
    console.error("Error loading data:", error);
    // Don't fall back to demo data
  }
}

// Populate account dropdowns
function populateAccountDropdowns() {
  console.log("populateAccountDropdowns called, accounts:", accounts);
  const fromAccount = document.getElementById("fromAccount");
  const toAccountInternal = document.getElementById("toAccountInternal");
  fromAccount.innerHTML = "";
  toAccountInternal.innerHTML = "";
  accounts.forEach((acc) => {
    console.log("Adding account:", acc);
    const last4 = acc.account_number ? acc.account_number.slice(-4) : "0000";
    const opt1 = document.createElement("option");
    opt1.value = acc.id;
    opt1.textContent = `${acc.type} ****${last4} $${acc.balance.toFixed(2)}`;
    fromAccount.appendChild(opt1);
  });
  updateToAccountInternal();
}
function updateToAccountInternal() {
  const fromId = document.getElementById("fromAccount").value;
  const toAccountInternal = document.getElementById("toAccountInternal");
  toAccountInternal.innerHTML = "";
  accounts.forEach((acc) => {
    if (acc.id != fromId) {
      const last4 = acc.account_number ? acc.account_number.slice(-4) : "0000";
      const opt2 = document.createElement("option");
      opt2.value = acc.id;
      opt2.textContent = `${acc.type} ****${last4} $${acc.balance.toFixed(2)}`;
      toAccountInternal.appendChild(opt2);
    }
  });
}

// Saved recipients UI
function renderSavedRecipients() {
  const savedDiv = document.getElementById("savedRecipients");
  savedDiv.innerHTML = "";
  if (savedRecipients.length > 0) {
    savedDiv.innerHTML = "<b>Saved Recipients:</b> ";
    savedRecipients.forEach((name) => {
      const span = document.createElement("span");
      span.textContent = name;
      span.onclick = () => {
        document.getElementById("toType").value = "external";
        document.getElementById("toType").dispatchEvent(new Event("change"));
        // Find the recipient's user_id from Django data
        if (djangoData && djangoData.recipients) {
          const recipient = djangoData.recipients.find((r) => r.name === name);
          if (recipient && recipient.user_id) {
            document.getElementById("toAccountExternalId").value =
              recipient.user_id;
            document
              .getElementById("toAccountExternalId")
              .dispatchEvent(new Event("input"));
          }
        }
      };
      savedDiv.appendChild(span);
    });
  }
}

// Payment form logic
const paymentForm = document.getElementById("paymentForm");
const toType = document.getElementById("toType");
const toAccountInternalDiv = document.getElementById("toAccountInternalDiv");
const toAccountExternalDiv = document.getElementById("toAccountExternalDiv");
const paymentSuccess = document.getElementById("paymentSuccess");
const paymentError = document.getElementById("paymentError");
const saveRecipientBtn = document.getElementById("saveRecipientBtn");
const toAccountExternalId = document.getElementById("toAccountExternalId");
const recipientInfo = document.getElementById("recipientInfo");
const recipientError = document.getElementById("recipientError");

let resolvedRecipient = null;

toType.addEventListener("change", function () {
  if (this.value === "internal") {
    toAccountInternalDiv.style.display = "";
    toAccountExternalDiv.style.display = "none";
  } else {
    toAccountInternalDiv.style.display = "none";
    toAccountExternalDiv.style.display = "";
  }
});

document
  .getElementById("fromAccount")
  .addEventListener("change", updateToAccountInternal);

// External recipient lookup
toAccountExternalId.addEventListener("input", async function () {
  const val = this.value.trim().toUpperCase();
  if (val.length === 0) {
    resolvedRecipient = null;
    recipientInfo.style.display = "none";
    recipientError.textContent = "";
    return;
  }

  try {
    const result = await apiCall(
      `/api/recipient/lookup/?user_id=${encodeURIComponent(val)}`
    );
    if (result.found) {
      resolvedRecipient = { userId: val, name: result.name };
      recipientInfo.textContent = `Name: ${result.name}`;
      recipientInfo.style.display = "";
      recipientError.textContent = "";
    } else {
      resolvedRecipient = null;
      recipientInfo.style.display = "none";
      recipientError.textContent = "User ID not found in Skandia Bank(SKB).";
    }
  } catch (error) {
    resolvedRecipient = null;
    recipientInfo.style.display = "none";
    recipientError.textContent = "Error looking up user ID.";
    console.error("Lookup error:", error);
  }
});

// Save recipient
saveRecipientBtn.addEventListener("click", async function () {
  if (resolvedRecipient) {
    const name = resolvedRecipient.name;
    if (!savedRecipients.includes(name)) {
      try {
        await apiCall("/api/recipient/save/", {
          method: "POST",
          body: JSON.stringify({
            user_id: resolvedRecipient.userId,
            name: name,
          }),
        });
        savedRecipients.push(name);
        renderSavedRecipients();
        paymentSuccess.textContent = "Recipient saved!";
        paymentSuccess.style.display = "";
        setTimeout(() => {
          paymentSuccess.style.display = "none";
        }, 2000);
      } catch (error) {
        paymentError.textContent = "Error saving recipient.";
        paymentError.style.display = "";
        setTimeout(() => {
          paymentError.style.display = "none";
        }, 2000);
        console.error("Save recipient error:", error);
      }
    }
  } else {
    paymentError.textContent = "Enter a valid User ID to save recipient.";
    paymentError.style.display = "";
    setTimeout(() => {
      paymentError.style.display = "none";
    }, 2000);
  }
});

// Confirmation modal logic
const confirmModalBg = document.getElementById("confirmModalBg");
const confirmDetails = document.getElementById("confirmDetails");
let confirmCallback = null;

document.getElementById("confirmYes").onclick = function () {
  confirmModalBg.classList.remove("show");
  // Show PIN modal
  document.getElementById("pinInput").value = "";
  document.getElementById("pinError").textContent = "";
  pinModalBg.classList.add("show");
};
document.getElementById("confirmNo").onclick = function () {
  confirmModalBg.classList.remove("show");
  paymentSuccess.style.display = "none";
  paymentError.style.display = "none";
};

document.getElementById("confirmYes").onclick = function () {
  confirmModalBg.classList.remove("show");
  // Process payment directly with Django authentication
  if (confirmCallback) confirmCallback();
};
document.getElementById("confirmNo").onclick = function () {
  confirmModalBg.classList.remove("show");
  paymentSuccess.style.display = "none";
  paymentError.style.display = "none";
};

paymentForm.addEventListener("submit", async function (e) {
  e.preventDefault();
  paymentSuccess.style.display = "none";
  paymentError.style.display = "none";

  const fromAccountId = document.getElementById("fromAccount").value;
  const fromAcc = accounts.find((acc) => acc.id == fromAccountId);
  let toAccountId, recipientUserId;
  let toTypeVal = toType.value;
  let amount = parseFloat(document.getElementById("amount").value);
  let category = document.getElementById("category").value;
  let note = document.getElementById("note").value.trim();
  let scheduleDate = document.getElementById("scheduleDate").value;
  let recurring = document.getElementById("recurring").value;

  if (isNaN(amount) || amount <= 0) {
    paymentError.textContent = "Please enter a valid amount.";
    paymentError.style.display = "";
    return;
  }

  if (!fromAcc) {
    paymentError.textContent = "Please select a valid from account.";
    paymentError.style.display = "";
    return;
  }

  if (toTypeVal === "internal") {
    toAccountId = document.getElementById("toAccountInternal").value;
    if (!toAccountId) {
      paymentError.textContent = "Please select a to account.";
      paymentError.style.display = "";
      return;
    }
    if (fromAccountId == toAccountId) {
      paymentError.textContent = "Cannot transfer to the same account.";
      paymentError.style.display = "";
      return;
    }
  } else {
    recipientUserId = toAccountExternalId.value.trim().toUpperCase();
    if (!recipientUserId || !resolvedRecipient) {
      paymentError.textContent = "Enter a valid Skandia Bank (SKB) User ID.";
      paymentError.style.display = "";
      return;
    }
  }

  // Confirmation dialog
  let confirmMsg = `<b>From:</b> ${fromAcc.type} (${fromAcc.number})<br>`;
  if (toTypeVal === "internal") {
    const toAcc = accounts.find((acc) => acc.id == toAccountId);
    confirmMsg += `<b>To:</b> ${toAcc.type} (${toAcc.number})<br>`;
  } else {
    confirmMsg += `<b>To:</b> ${resolvedRecipient.name} (${recipientUserId})<br>`;
  }
  confirmMsg += `<b>Amount:</b> $${amount.toFixed(2)}<br>`;
  confirmMsg += `<b>Category:</b> ${category}<br>`;
  if (note) confirmMsg += `<b>Note:</b> ${note}<br>`;
  if (scheduleDate) confirmMsg += `<b>Scheduled for:</b> ${scheduleDate}<br>`;
  if (recurring !== "none")
    confirmMsg += `<b>Recurring:</b> ${
      recurring.charAt(0).toUpperCase() + recurring.slice(1)
    }<br>`;
  confirmDetails.innerHTML = confirmMsg;
  confirmModalBg.classList.add("show");

  confirmCallback = async function () {
    try {
      const paymentData = {
        from_account: fromAccountId,
        to_type: toTypeVal,
        amount: amount,
        category: category,
        note: note,
        schedule_date: scheduleDate || null,
        recurring: recurring,
      };

      if (toTypeVal === "internal") {
        paymentData.to_account = toAccountId;
      } else {
        paymentData.recipient_user_id = recipientUserId;
      }

      const result = await apiCall("/api/payment/create/", {
        method: "POST",
        body: JSON.stringify(paymentData),
      });

      if (result.success) {
        paymentSuccess.textContent = result.message;
        paymentSuccess.style.display = "";
        paymentForm.reset();

        // Reload the page to get updated data
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        paymentError.textContent = result.error || "Payment failed.";
        paymentError.style.display = "";
      }
    } catch (error) {
      paymentError.textContent = "Error processing payment.";
      paymentError.style.display = "";
      console.error("Payment error:", error);
    }
  };
});

function renderPaymentHistory() {
  const paymentHistoryList = document.getElementById("paymentHistory");
  paymentHistoryList.innerHTML = "";
  if (paymentHistory.length === 0) {
    paymentHistoryList.innerHTML = "<li>No payments yet.</li>";
    return;
  }
  paymentHistory.forEach((pay) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>
          ${pay.date} <small>${pay.from} &rarr; ${pay.to} (${
      pay.category
    })</small>
          <br><small style="color:#888;">${pay.note ? pay.note : ""}</small>
          </span>
          <span style="font-weight:bold; color:#0a2540;">
            -$${pay.amount.toFixed(2)}<br>
            <span style="font-size:0.9em;color:${
              pay.status === "Completed" ? "#388e3c" : "#d32f2f"
            }">${pay.status}</span>
          </span>`;
    paymentHistoryList.appendChild(li);
  });
}

function renderScheduledPayments() {
  const scheduledList = document.getElementById("scheduledPayments");
  scheduledList.innerHTML = "";
  if (scheduledPayments.length === 0) {
    scheduledList.innerHTML = "<li>No scheduled payments.</li>";
    return;
  }
  scheduledPayments.forEach((pay) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>
          ${pay.date} <small>${pay.from} &rarr; ${pay.to} (${
      pay.category
    })</small>
          <br><small style="color:#888;">${pay.note ? pay.note : ""}</small>
          </span>
          <span style="font-weight:bold; color:#0a2540;">
            -$${pay.amount.toFixed(2)}<br>
            <span style="font-size:0.9em;color:#0072ce">${pay.status}${
      pay.recurring !== "none" ? " (" + pay.recurring + ")" : ""
    }</span>
          </span>`;
    scheduledList.appendChild(li);
  });
}

// Export CSV
function exportCSV() {
  let csv = "Date,From,To,Amount,Category,Note,Status,Recurring\n";
  paymentHistory.forEach((pay) => {
    csv +=
      [
        pay.date,
        pay.from,
        pay.to,
        pay.amount,
        pay.category,
        `"${pay.note.replace(/"/g, '""')}"`,
        pay.status,
        pay.recurring,
      ].join(",") + "\n";
  });
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "payment_history.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
window.exportCSV = exportCSV;

// Analytics (simple bar chart)
function renderAnalytics() {
  const canvas = document.getElementById("analyticsChart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Prepare data
  const last7 = paymentHistory.slice(0, 7).reverse();
  const maxAmt = Math.max(...last7.map((p) => p.amount), 100);
  const barWidth = (canvas.width - 40) / 7;
  ctx.font = "12px Arial";
  ctx.fillStyle = "#0a2540";
  ctx.fillText("Amount ($)", 5, 15);
  last7.forEach((p, i) => {
    const x = 30 + i * barWidth;
    const y = canvas.height - 30;
    const h = Math.max(10, (p.amount / maxAmt) * (canvas.height - 60));
    ctx.fillStyle = "#0072ce";
    ctx.fillRect(x, y - h, barWidth - 10, h);
    ctx.fillStyle = "#0a2540";
    ctx.fillText("-$" + p.amount.toFixed(0), x, y - h - 5);
    ctx.save();
    ctx.translate(x + barWidth / 2 - 10, y + 15);
    ctx.rotate(-Math.PI / 6);
    ctx.fillText(p.category, 0, 0);
    ctx.restore();
  });
  ctx.strokeStyle = "#e5e7eb";
  ctx.beginPath();
  ctx.moveTo(25, canvas.height - 30);
  ctx.lineTo(canvas.width - 10, canvas.height - 30);
  ctx.stroke();
}

// Initial population
(async function init() {
  initializeData(); // Initialize data first
  await loadData(); // Then load from APIs if needed
  populateAccountDropdowns();
  renderSavedRecipients();
  renderPaymentHistory();
  renderScheduledPayments();
  setTimeout(renderAnalytics, 100);
})();

// Responsive: update toAccountInternal when fromAccount changes
document
  .getElementById("fromAccount")
  .addEventListener("change", updateToAccountInternal);

// Redraw analytics on window resize
window.addEventListener("resize", () => setTimeout(renderAnalytics, 200));
