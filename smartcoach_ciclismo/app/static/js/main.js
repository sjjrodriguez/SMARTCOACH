// General client-side logic.
document.addEventListener("DOMContentLoaded", function () {
    // Success and info messages close by themselves after 6 seconds.
    document.querySelectorAll(".alert[data-autodismiss]").forEach(function (el) {
        setTimeout(function () {
            if (window.bootstrap && document.body.contains(el)) {
                bootstrap.Alert.getOrCreateInstance(el).close();
            }
        }, 6000);
    });

    // Forms with data-confirm ask for confirmation before submitting
    // (used for destructive actions such as deleting a workout).
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    // Avoid double submissions: disable the submit button once the form is sent.
    document.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (event.defaultPrevented) return;
            form.querySelectorAll("button[type=submit]").forEach(function (btn) {
                // Defer so the browser still sends the form before the button is disabled.
                setTimeout(function () { btn.disabled = true; }, 0);
            });
        });
    });
});

// Re-enable buttons when the page is restored from the back/forward cache.
window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        document.querySelectorAll("button[type=submit]").forEach(function (btn) {
            btn.disabled = false;
        });
    }
});
