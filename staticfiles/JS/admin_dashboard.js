lucide.createIcons();

function openModal(
  name,
  id,
  email,
  country_code,
  phone,
  ssn,
  id_type,
  id_front,
  id_back
) {
  const modal = document.getElementById("userModal");
  const info = document.getElementById("modalInfo");

  info.innerHTML = `
                                  <div style="margin-bottom: 1.5rem; display: flex; align-items: center; gap: 15px;">
                                      <div style="width: 60px; height: 60px; background: #f1f5f9; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 800; color: var(--primary)">${name
                                        .split(" ")
                                        .map((n) => n[0])
                                        .join("")}</div>
                                      <div>
                                          <h3 style="font-size: 1.2rem; color: var(--primary)">${name}</h3>
                                          <p style="color: var(--text-muted); font-size: 0.9rem;">Client ID: ${id}</p>
                                      </div>
                                  </div>
                                  <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">First Name</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${
                                            name.split(" ")[0]
                                          }</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Last Name</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${
                                            name.split(" ")[1] || ""
                                          }</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">User ID</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${id}</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Email</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${email}</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Country Code</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${
                                            country_code === "+1"
                                              ? "USA" + country_code
                                              : country_code
                                          }</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Phone</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${phone}</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">SSN</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${ssn}</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">ID Type</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${id_type}</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">ID Front</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${
                                            id_front
                                              ? '<img src="' +
                                                id_front +
                                                '" alt="ID Front" style="max-width:100%; max-height:100px;">'
                                              : "No file"
                                          }</div>
                                      </div>
                                      <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid var(--border)">
                                          <span style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">ID Back</span>
                                          <div style="font-weight: 800; font-size: 1.1rem;">${
                                            id_back
                                              ? '<img src="' +
                                                id_back +
                                                '" alt="ID Back" style="max-width:100%; max-height:100px;">'
                                              : "No file"
                                          }</div>
                                      </div>
                                  </div>
                              `;
  modal.style.display = "flex";
}

function closeModal() {
  document.getElementById("userModal").style.display = "none";
}

window.onclick = function (e) {
  if (e.target == document.getElementById("userModal")) closeModal();
};

function updateUnreadStatus() {
  fetch(unreadStatusUrl)
    .then((response) => response.json())
    .then((data) => {
      // Update the live chat status
      const liveChatCard = document.querySelector(
        ".status-grid .mini-card:nth-child(2)"
      );
      const beeper = liveChatCard.querySelector(".beeper");
      const statusDiv = liveChatCard.querySelector(
        "div:last-child div:last-child"
      );
      if (data.has_any_unread) {
        beeper.classList.add("active");
        statusDiv.textContent = "New Message Alert";
      } else {
        beeper.classList.remove("active");
        statusDiv.textContent = "All Clear";
      }

      // Update customer badges
      const userRows = document.querySelectorAll("#userList .user-row");
      userRows.forEach((row) => {
        const userIdElement = row.querySelector(
          "div:nth-child(2) div:last-child"
        );
        if (userIdElement) {
          const userId = userIdElement.textContent.trim();
          const wrapper = row.querySelector(".chat-btn-wrapper");
          const badge = wrapper.querySelector(".chat-badge");
          if (data.unread_customers[userId]) {
            if (!badge) {
              const newBadge = document.createElement("span");
              newBadge.className = "chat-badge";
              wrapper.appendChild(newBadge);
            }
          } else {
            if (badge) {
              badge.remove();
            }
          }
        }
      });
    })
    .catch((error) => console.error("Error updating unread status:", error));
}

// Poll every 5 seconds
setInterval(updateUnreadStatus, 5000);

// Initial update
updateUnreadStatus();
