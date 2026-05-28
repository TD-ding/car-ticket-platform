document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss alerts after 4 seconds
    document.querySelectorAll(".alert").forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity .4s";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        }, 4000);
    });

    // Prevent double-click form submission
    document.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function () {
            var btn = form.querySelector('button[type="submit"]');
            if (btn && !btn.disabled) {
                btn.disabled = true;
                var original = btn.textContent;
                btn.textContent = original + "...";
                setTimeout(function () {
                    btn.disabled = false;
                    btn.textContent = original;
                }, 5000);
            }
        });
    });

    // Mobile hamburger menu toggle
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    if (toggle && links) {
        toggle.addEventListener("click", function () {
            links.classList.toggle("nav-open");
        });
        // Close menu when a link is clicked
        links.querySelectorAll("a").forEach(function (a) {
            a.addEventListener("click", function () {
                links.classList.remove("nav-open");
            });
        });
    }
});
