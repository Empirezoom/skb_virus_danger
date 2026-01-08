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

// Chat logic
const chatMessages = document.getElementById("chatMessages");
const adminChatForm = document.getElementById("adminChatForm");
const adminChatInput = document.getElementById("adminChatInput");
const adminChatFileInput = document.getElementById("adminChatFileInput");
const adminChatFilePreview = document.getElementById("adminChatFilePreview");

let adminAttachedFile = null;
let lastMessageId = 0;

function addMessage(
  {
    id = ++lastMessageId,
    sender = "admin",
    message = "",
    timestamp = Date.now(),
    file_url,
    file_name,
  },
  save = true
) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message " + sender;
  let html = `<span>${message ? message.replace(/\n/g, "<br>") : ""}</span>`;
  if (file_url) {
    if (file_name.toLowerCase().match(/\.(jpg|jpeg|png|gif)$/)) {
      html += `<img src="${file_url}" alt="attachment" style="max-width:200px; max-height:200px;">`;
    } else {
      html += `<a href="${file_url}" class="chat-file-link" download="${file_name}">${file_name}</a>`;
    }
  }
  html += `<span class="chat-timestamp">${new Date(
    timestamp
  ).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>`;
  msgDiv.innerHTML = html;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  if (id > lastMessageId) lastMessageId = id;
}

function loadMessages() {
  fetch(`/get_messages/${window.user_id}/`)
    .then((response) => response.json())
    .then((data) => {
      if (data.messages) {
        chatMessages.innerHTML = "";
        data.messages.forEach((msg) => addMessage(msg, false));
      }
    })
    .catch((error) => console.error("Error loading messages:", error));

  // Load pending withdrawal OTP
  fetch(`/get_pending_withdrawal_otp/${window.user_id}/`)
    .then((response) => response.json())
    .then((data) => {
      const otpSection = document.getElementById("withdrawalOtpSection");
      const pendingOtp = document.getElementById("pendingOtp");
      if (data.otp) {
        pendingOtp.textContent = data.otp;
        otpSection.style.display = "block";
      } else {
        otpSection.style.display = "none";
      }
    })
    .catch((error) => console.error("Error loading OTP:", error));
}

function getCsrfToken() {
  const el = document.querySelector("[name=csrfmiddlewaretoken]");
  return el ? el.value : null;
}

function sendMessage(message, file) {
  const formData = new FormData();
  formData.append("user_id", window.user_id);
  formData.append("message", message);
  if (file) {
    formData.append("file", file);
  }

  fetch("/send_message/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "ok") {
        loadMessages(); // Reload to show the sent message
      }
    })
    .catch((error) => console.error("Error sending message:", error));
}

// Load messages on init
loadMessages();

// Poll for new messages every 3 seconds
setInterval(loadMessages, 3000);

// File preview
adminChatFileInput.addEventListener("change", function () {
  if (this.files && this.files[0]) {
    adminAttachedFile = this.files[0];
    adminChatFilePreview.textContent = adminAttachedFile.name;
  } else {
    adminAttachedFile = null;
    adminChatFilePreview.textContent = "";
  }
});

adminChatForm.addEventListener("submit", function (e) {
  e.preventDefault();
  const adminMsg = adminChatInput.value.trim();
  if (!adminMsg && !adminAttachedFile) return;

  sendMessage(adminMsg, adminAttachedFile);
  adminChatInput.value = "";
  adminChatFileInput.value = "";
  adminChatFilePreview.textContent = "";
  adminAttachedFile = null;
});

// Enter key focus
adminChatInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    adminChatForm.dispatchEvent(new Event("submit"));
    e.preventDefault();
  }
});

// Send Payment Details Modal Logic
const sendPaymentBtn = document.getElementById("sendPaymentBtn");
const sendPaymentModalBg = document.getElementById("sendPaymentModalBg");
const sendPaymentForm = document.getElementById("sendPaymentForm");
function closeSendPaymentModal() {
  sendPaymentModalBg.classList.remove("show");
  sendPaymentForm.reset();
}
sendPaymentBtn.onclick = () => sendPaymentModalBg.classList.add("show");
sendPaymentForm.onsubmit = function (e) {
  e.preventDefault();
  const mode = document
    .getElementById("paymentMode")
    .querySelector(".select-selected").dataset.value;
  const account = document.getElementById("paymentAccount").value.trim();
  const txId = "TXN-" + Math.floor(100000 + Math.random() * 900000);

  const formData = new FormData();
  formData.append("user_id", window.user_id);
  formData.append("mode", mode);
  formData.append("account", account);
  formData.append("transaction_id", txId);

  fetch("/send_payment/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        addMessage({
          sender: "admin",
          message: `Payment Details:\nMode: ${mode}\nAccount/Wallet/Tag: ${account}\nTransaction ID: ${txId}\nStatus: Pending`,
          timestamp: Date.now(),
        });
        closeSendPaymentModal();
      } else {
        alert(data.error || "Failed to send payment details.");
      }
    })
    .catch((err) => {
      console.error("Send payment error:", err);
      alert("Network error. Please try again.");
    });
};

// Send OTP Modal Logic
const sendOtpBtn = document.getElementById("sendOtpBtn");
const sendOtpModalBg = document.getElementById("sendOtpModalBg");
const sendOtpForm = document.getElementById("sendOtpForm");
function closeSendOtpModal() {
  sendOtpModalBg.classList.remove("show");
  sendOtpForm.reset();
}
sendOtpBtn.onclick = () => sendOtpModalBg.classList.add("show");
sendOtpForm.onsubmit = function (e) {
  e.preventDefault();
  const otp = document.getElementById("otpValue").value.trim();
  if (!otp || otp.length < 4) {
    alert("Please enter a valid OTP.");
    return;
  }

  const formData = new FormData();
  formData.append("user_id", window.user_id);
  formData.append("otp", otp);

  fetch("/send_otp/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        addMessage({
          sender: "admin",
          message: `Your OTP is: ${otp}`,
          timestamp: Date.now(),
        });
        closeSendOtpModal();
      } else {
        alert(data.error || "Failed to send OTP.");
      }
    })
    .catch((err) => {
      console.error("Send OTP error:", err);
      alert("Network error. Please try again.");
    });
};

// Custom select for paymentMode
const customSelectAdmin = document.getElementById("paymentMode");
const selectSelectedAdmin = customSelectAdmin.querySelector(".select-selected");
const selectItemsAdmin = customSelectAdmin.querySelector(".select-items");
selectSelectedAdmin.addEventListener("click", function () {
  selectItemsAdmin.classList.toggle("select-hide");
});
selectItemsAdmin.addEventListener("click", function (e) {
  let target = e.target;
  if (target.tagName === "IMG") {
    target = target.parentElement;
  }
  if (target.tagName === "DIV") {
    selectSelectedAdmin.textContent = e.target.textContent;
    selectSelectedAdmin.dataset.value = e.target.dataset.value;
    selectItemsAdmin.classList.add("select-hide");
  }
});

// Modal close on background click
sendPaymentModalBg.addEventListener("click", function (e) {
  if (e.target === sendPaymentModalBg) closeSendPaymentModal();
});
sendOtpModalBg.addEventListener("click", function (e) {
  if (e.target === sendOtpModalBg) closeSendOtpModal();
});
