// Workout form: RPE picker, fatigue slider, quick-fill chips, note tags and a live summary.
(function () {
    "use strict";

    const form = document.getElementById("workout-form");
    if (!form) return;

    const $ = (id) => document.getElementById(id);
    const duration = $("duration_min");
    const distance = $("distance_km");
    const notes = $("notes");
    const fatigue = $("perceived_fatigue");

    const RPE_TEXT = {
        1: "Very easy: barely any effort.",
        2: "Easy: you could ride like this all day.",
        3: "Light: comfortable, full conversation.",
        4: "Steady: full sentences, breathing a little deeper.",
        5: "Moderate: short sentences, you feel the work.",
        6: "Somewhat hard: you can talk, but you would rather not.",
        7: "Hard: a few words at a time.",
        8: "Very hard: you can hold this for only a short while.",
        9: "Near maximal: hanging on until the end of the interval.",
        10: "Maximal: nothing left, all-out effort.",
    };
    const FATIGUE_TEXT = ["", "fresh", "fresh", "fine", "fine", "tired", "tired", "heavy", "very heavy", "drained", "exhausted"];

    function currentRpe() {
        const checked = form.querySelector("input[name=rpe]:checked");
        return checked ? Number(checked.value) : null;
    }

    function intensityLabel(rpe) {
        if (rpe <= 3) return "Easy";
        if (rpe <= 6) return "Moderate";
        if (rpe <= 8) return "Hard";
        return "Maximal";
    }

    function update() {
        const rpe = currentRpe();
        $("rpe-desc").textContent = rpe ? RPE_TEXT[rpe] : "Pick a number: 1 is very easy, 10 is maximal effort.";

        const f = Number(fatigue.value);
        $("fatigue-out").textContent = f;
        $("fatigue-desc").textContent = "(" + FATIGUE_TEXT[f] + ")";

        const min = Number(duration.value);
        const km = Number(distance.value);
        const hasTime = min > 0;

        $("sum-speed").textContent = hasTime && km > 0 ? (km / (min / 60)).toFixed(1) + " km/h" : "\u2013";
        // Same formula as the server (workouts.py): duration x RPE x 1.1 / 10.
        $("sum-tss").textContent = hasTime && rpe ? Math.round((min * rpe * 1.1) / 10) : "\u2013";
        $("sum-intensity").textContent = rpe ? intensityLabel(rpe) : "\u2013";

        const plan = $("sum-plan");
        if (plan) {
            const pm = Number(plan.dataset.minutes);
            const pk = Number(plan.dataset.km);
            const parts = [];
            if (hasTime) parts.push((min >= pm ? "+" : "") + Math.round(min - pm) + " min");
            if (km > 0) parts.push((km >= pk ? "+" : "") + (km - pk).toFixed(1) + " km");
            plan.textContent = parts.length ? parts.join(", ") + " vs plan" : "\u2013";
        }

        $("notes-count").textContent = notes.value.length;
        form.querySelectorAll("[data-tag]").forEach(function (btn) {
            btn.setAttribute("aria-pressed", String(notes.value.includes(btn.dataset.tag)));
            btn.classList.toggle("active", notes.value.includes(btn.dataset.tag));
        });
    }

    // Quick-fill chips for duration and distance.
    form.querySelectorAll("[data-quick-for]").forEach(function (group) {
        const input = $(group.dataset.quickFor);
        group.addEventListener("click", function (e) {
            const btn = e.target.closest("button[data-value]");
            if (!btn) return;
            input.value = btn.dataset.value;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.focus();
        });
    });

    // Note tags toggle a phrase in the textarea.
    $("note-tags").addEventListener("click", function (e) {
        const btn = e.target.closest("button[data-tag]");
        if (!btn) return;
        const tag = btn.dataset.tag;
        if (notes.value.includes(tag)) {
            notes.value = notes.value.replace(new RegExp("(, )?" + tag + "(, )?"), function (m, a, b) { return a && b ? ", " : ""; });
        } else {
            notes.value = notes.value.trim() ? notes.value.trim().replace(/[.,]$/, "") + ", " + tag : tag;
        }
        notes.value = notes.value.slice(0, Number(notes.maxLength) || 500);
        update();
    });

    form.addEventListener("input", update);
    form.addEventListener("change", update);
    update();
})();
