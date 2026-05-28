// Auto-dismiss alerts after 4 seconds
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".alert").forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity .4s";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        }, 4000);
    });
});
