// Graficas del dashboard con Chart.js.
// Lee los datos del <script id="dashboard-data" type="application/json">.
(function () {
    "use strict";

    const dataEl = document.getElementById("dashboard-data");
    if (!dataEl || typeof Chart === "undefined") return;

    let data;
    try {
        data = JSON.parse(dataEl.textContent);
    } catch (err) {
        console.error("No se pudieron leer los datos del dashboard:", err);
        return;
    }

    // Colores y fuente salen de style.css para que todo el sitio coincida.
    const css = getComputedStyle(document.documentElement);
    const token = (name, fallback) => css.getPropertyValue(name).trim() || fallback;
    const primary = token("--sc-primary", "#0d6efd");
    const ink = token("--sc-ink", "#1c2430");
    const line = token("--sc-line", "#dde3ea");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    Chart.defaults.font.family = token("--sc-font", "system-ui, sans-serif");
    Chart.defaults.font.size = 13;
    Chart.defaults.color = ink;
    Chart.defaults.animation = reduceMotion ? false : { duration: 500 };

    const baseOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` Carga: ${ctx.parsed.y}` } },
        },
        scales: {
            x: { grid: { display: false } },
            y: {
                beginAtZero: true,
                grid: { color: line },
                title: { display: true, text: "Carga de entrenamiento" },
            },
        },
    };

    // 1) Carga por dia: el dia de hoy (ultima barra) se resalta.
    const dailyCanvas = document.getElementById("chart-daily");
    if (dailyCanvas) {
        const n = data.daily.values.length;
        new Chart(dailyCanvas, {
            type: "bar",
            data: {
                labels: data.daily.labels,
                datasets: [{
                    data: data.daily.values,
                    backgroundColor: data.daily.values.map((_, i) => (i === n - 1 ? primary : primary + "88")),
                    borderRadius: 4,
                }],
            },
            options: baseOptions,
        });
    }

    // 2) Carga por semana: tendencia de las ultimas 8 semanas.
    const weeklyCanvas = document.getElementById("chart-weekly");
    if (weeklyCanvas) {
        new Chart(weeklyCanvas, {
            type: "line",
            data: {
                labels: data.weekly.labels,
                datasets: [{
                    data: data.weekly.values,
                    borderColor: primary,
                    backgroundColor: primary,
                    pointRadius: 4,
                    borderWidth: 2,
                    tension: 0.25,
                }],
            },
            options: {
                ...baseOptions,
                scales: {
                    ...baseOptions.scales,
                    x: { grid: { display: false }, title: { display: true, text: "Semana (inicio)" } },
                },
            },
        });
    }
})();