// Grafica de carga semanal (Chart.js).
// Requiere en la vista: <canvas id="cargaSemanal"></canvas> y Chart.js cargado antes de este archivo.
(function () {
    "use strict";

    var canvas = document.getElementById("cargaSemanal");
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    // Envuelve el canvas en .sc-chart (la altura se controla desde style.css).
    if (!canvas.parentElement.classList.contains("sc-chart")) {
        var wrap = document.createElement("div");
        wrap.className = "sc-chart";
        canvas.parentNode.insertBefore(wrap, canvas);
        wrap.appendChild(canvas);
    }

    // Lee los colores y la tipografia de las variables de style.css.
    var css = getComputedStyle(document.documentElement);
    function cssVar(name) {
        return css.getPropertyValue(name).trim();
    }
    var colors = {
        bar: cssVar("--sc-primary"),
        text: cssVar("--sc-muted"),
        grid: cssVar("--sc-line")
    };

    Chart.defaults.font.family = cssVar("--sc-font");
    Chart.defaults.font.size = 14;
    Chart.defaults.color = colors.text;

    // TODO backend: definir window.cargaSemanal = {labels: [...], values: [...]} desde la plantilla
    // (por ejemplo con {{ carga_semanal|tojson }}). Mientras no exista, se usan datos de ejemplo.
    var datos = window.cargaSemanal || {
        labels: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
        values: [0, 60, 75, 40, 0, 150, 60]
    };

    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "Gráfica de barras con los minutos entrenados cada día de la semana");

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: datos.labels,
            datasets: [{
                label: "Carga (min)",
                data: datos.values,
                backgroundColor: colors.bar,
                borderRadius: 4,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.text }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: colors.grid },
                    ticks: { color: colors.text },
                    title: { display: true, text: "Minutos", color: colors.text }
                }
            }
        }
    });
})();