
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

      // FAQ toggle logic
      document.querySelectorAll(".faq-question").forEach((btn) => {
        btn.addEventListener("click", function () {
          const answer = this.nextElementSibling;
          answer.classList.toggle("show");
        });
      });

      // Support form logic
      const supportForm = document.getElementById("supportForm");
      const supportSuccess = document.getElementById("supportSuccess");
      const supportError = document.getElementById("supportError");
      supportForm.addEventListener("submit", function (e) {
        e.preventDefault();
        supportSuccess.style.display = "none";
        supportError.style.display = "none";
        const name = document.getElementById("supportName").value.trim();
        const email = document.getElementById("supportEmail").value.trim();
        const topic = document.getElementById("supportTopic").value;
        const message = document.getElementById("supportMessage").value.trim();
        if (!name || !email || !topic || !message) {
          supportError.textContent = "Please fill in all fields.";
          supportError.style.display = "";
          return;
        }
        // Simulate sending
        setTimeout(() => {
          supportSuccess.textContent =
            "Your request has been submitted! Our team will contact you soon.";
          supportSuccess.style.display = "";
          supportForm.reset();
        }, 800);
      });
    
