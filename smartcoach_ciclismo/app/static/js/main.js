// Logica general del cliente.
document.addEventListener("DOMContentLoaded", function () {
    // Las alertas con data-autodismiss se cierran solas a los 5 segundos.
    var AUTODISMISS_MS = 5000;

    document.querySelectorAll(".alert[data-autodismiss]").forEach(function (el) {
        setTimeout(function () {
            if (window.bootstrap && document.body.contains(el)) {
                bootstrap.Alert.getOrCreateInstance(el).close();
            }
        }, AUTODISMISS_MS);
    });
});