// Logica general del cliente.
document.addEventListener("DOMContentLoaded", function () {
    // Los mensajes de exito e informacion se cierran solos a los 6 segundos.
    document.querySelectorAll(".alert[data-autodismiss]").forEach(function (el) {
        setTimeout(function () {
            if (window.bootstrap && document.body.contains(el)) {
                bootstrap.Alert.getOrCreateInstance(el).close();
            }
        }, 6000);
    });
});