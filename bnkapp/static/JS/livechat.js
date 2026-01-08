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
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatFileInput = document.getElementById("chatFileInput");
const chatFilePreview = document.getElementById("chatFilePreview");

let attachedFile = null;
let lastMessageId = 0;

function addMessage(
  {
    id = ++lastMessageId,
    sender = "user",
    message = "",
    timestamp = Date.now(),
    file_url,
    file_name,
  },
  save = true
) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message " + (sender === "user" ? "user" : "agent");
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
      } else {
        console.error("Send message failed:", data);
      }
    })
    .catch((error) => console.error("Error sending message:", error));
}

// Load messages on init
loadMessages();

// Poll for new messages every 3 seconds
setInterval(loadMessages, 3000);

// File preview
chatFileInput.addEventListener("change", function () {
  if (this.files && this.files[0]) {
    attachedFile = this.files[0];
    chatFilePreview.textContent = attachedFile.name;
  } else {
    attachedFile = null;
    chatFilePreview.textContent = "";
  }
});

chatForm.addEventListener("submit", function (e) {
  e.preventDefault();
  const userMsg = chatInput.value.trim();
  if (!userMsg && !attachedFile) return;

  sendMessage(userMsg, attachedFile);
  chatInput.value = "";
  chatFileInput.value = "";
  chatFilePreview.textContent = "";
  attachedFile = null;
});

// Enter key focus
chatInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    chatForm.dispatchEvent(new Event("submit"));
    e.preventDefault();
  }
});

// Add Balance Modal Logic
const addBalanceBtn = document.getElementById("addBalanceBtn");
const addBalanceModalBg = document.getElementById("addBalanceModalBg");
const addBalanceForm = document.getElementById("addBalanceForm");
function closeAddBalanceModal() {
  addBalanceModalBg.classList.remove("show");
  addBalanceForm.reset();
}
addBalanceBtn.onclick = () => addBalanceModalBg.classList.add("show");
addBalanceForm.onsubmit = function (e) {
  e.preventDefault();
  const name = document.getElementById("addAccountName").value.trim();
  const mode = document
    .getElementById("addMode")
    .querySelector(".select-selected").dataset.value;
  const amount = document.getElementById("addAmount").value;

  const formData = new FormData();
  formData.append("user_id", window.user_id);
  formData.append("account_name", name);
  formData.append("mode", mode);
  formData.append("amount", amount);

  fetch("/add_balance/", {
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
          sender: "user",
          message: `Add Balance Request:\nAccount Name: ${name}\nMode: ${mode}\nAmount: $${amount}\n\nPlease wait for admin to send payment details for your selected mode.`,
          timestamp: Date.now(),
        });
        closeAddBalanceModal();
      } else {
        alert(data.error || "Failed to submit add balance request.");
      }
    })
    .catch((err) => {
      console.error("Add balance error:", err);
      alert("Network error. Please try again.");
    });
};

// Withdrawal Modal Logic
const withdrawBtn = document.getElementById("withdrawBtn");
const withdrawModalBg = document.getElementById("withdrawModalBg");
const withdrawForm = document.getElementById("withdrawForm");
const withdrawNextBtn = document.getElementById("withdrawNextBtn");
const otpSection = document.getElementById("otpSection");
const withdrawSubmitBtn = document.getElementById("withdrawSubmitBtn");

// Store withdrawal data to persist it across form interactions
let pendingWithdrawalData = null;

function closeWithdrawModal() {
  withdrawModalBg.classList.remove("show");
  withdrawForm.reset();
  otpSection.style.display = "none";
  withdrawNextBtn.style.display = "";
  pendingWithdrawalData = null;
}
withdrawBtn.onclick = () => withdrawModalBg.classList.add("show");
withdrawNextBtn.onclick = function (e) {
  e.preventDefault();
  // Validate withdrawal fields
  const bank = document.getElementById("withdrawBank").value.trim();
  const account = document.getElementById("withdrawAccount").value.trim();
  const routing = document.getElementById("withdrawRouting").value.trim();
  const amount = document.getElementById("withdrawAmount").value.trim();
  if (!bank || !account || !routing || !amount) {
    alert("Please fill all withdrawal fields.");
    return;
  }
  // Store the data before sending to server
  pendingWithdrawalData = {
    bank: bank,
    account: account,
    routing: routing,
    amount: amount,
  };
  // Send to generate OTP
  const formData = new FormData();
  formData.append("user_id", window.user_id);
  formData.append("bank", bank);
  formData.append("account", account);
  formData.append("routing", routing);
  formData.append("amount", amount);

  fetch("/generate_withdrawal_otp/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        otpSection.style.display = "block";
        withdrawNextBtn.style.display = "none";
      } else {
        alert(data.error || "Failed to generate OTP.");
        pendingWithdrawalData = null;
      }
    })
    .catch((err) => {
      console.error("Generate OTP error:", err);
      alert("Network error. Please try again.");
      pendingWithdrawalData = null;
    });
};
withdrawSubmitBtn.onclick = function (e) {
  e.preventDefault();
  const otp = document.getElementById("withdrawOtp").value.trim();
  if (!otp) {
    alert("Please enter the OTP.");
    return;
  }
  if (!pendingWithdrawalData) {
    alert("Withdrawal data not found. Please try again.");
    return;
  }
  // Prepare data
  const formData = new FormData();
  formData.append("user_id", window.user_id);
  formData.append("otp", otp);

  fetch("/withdraw/", {
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
          sender: "user",
          message: `Withdrawal Request:\nBank: ${pendingWithdrawalData.bank}\nAccount: ${pendingWithdrawalData.account}\nRecipient Account Name: ${pendingWithdrawalData.routing}\nAmount: $${pendingWithdrawalData.amount}\n\nWithdrawal info submitted. Please wait for admin approval.`,
          timestamp: Date.now(),
        });
        closeWithdrawModal();
      } else {
        alert(data.error || "Failed to submit withdrawal request.");
      }
    })
    .catch((err) => {
      console.error("Withdrawal error:", err);
      alert("Network error. Please try again.");
    });
};
// Custom select for addMode
const customSelect = document.getElementById("addMode");
const selectSelected = customSelect.querySelector(".select-selected");
const selectItems = customSelect.querySelector(".select-items");
selectSelected.addEventListener("click", function () {
  selectItems.classList.toggle("select-hide");
});
selectItems.addEventListener("click", function (e) {
  let target = e.target;
  if (target.tagName === "IMG") {
    target = target.parentElement;
  }
  if (target.tagName === "DIV") {
    selectSelected.textContent = target.textContent;
    selectSelected.dataset.value = target.dataset.value;
    selectItems.classList.add("select-hide");
  }
});
// Modal close on background click
addBalanceModalBg.addEventListener("click", function (e) {
  if (e.target === addBalanceModalBg) closeAddBalanceModal();
});
withdrawModalBg.addEventListener("click", function (e) {
  if (e.target === withdrawModalBg) closeWithdrawModal();
});
