// Plan page: week pills, day list and a detail panel (Workout / Recovery / Fuel).
// Data comes from <script id="routine-data" type="application/json">.
(function () {
    "use strict";

    const dataEl = document.getElementById("routine-data");
    const listEl = document.getElementById("day-list");
    if (!dataEl || !listEl) return;

    let data;
    try {
        data = JSON.parse(dataEl.textContent);
    } catch (err) {
        console.error("Could not read the plan data:", err);
        return;
    }

    const pillsEl = document.getElementById("week-pills");
    const summaryEl = document.getElementById("week-summary");
    const detailEl = document.getElementById("day-detail");
    const state = { week: data.selected.week, day: data.selected.day, tab: "workout" };

    // Tiny DOM helper. Text always goes through textContent (never innerHTML).
    function h(tag, attrs, children) {
        const el = document.createElement(tag);
        Object.entries(attrs || {}).forEach(function ([k, v]) {
            if (v === false || v == null) return;
            if (k === "class") el.className = v;
            else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
            else el.setAttribute(k, v === true ? "" : v);
        });
        [].concat(children == null ? [] : children).forEach(function (c) {
            if (c == null || c === false) return; // allow conditional children
            el.append(c.nodeType ? c : document.createTextNode(c));
        });
        return el;
    }

    const duration = (min) => (min >= 60 ? Math.floor(min / 60) + " h " + (min % 60 ? (min % 60) + " min" : "") : min + " min").trim();
    const week = () => data.weeks[state.week];
    const day = () => week().days[state.day];

    function statusOf(d) {
        if (d.is_rest) return { text: "Rest", cls: "rest" };
        if (d.done) return { text: "Done", cls: "done" };
        if (d.is_today) return { text: "Today", cls: "today" };
        if (d.is_past) return { text: "Missed", cls: "missed" };
        return null;
    }

    function renderPills() {
        pillsEl.replaceChildren.apply(pillsEl, data.weeks.map(function (w, i) {
            return h("button", {
                type: "button", role: "tab", "aria-selected": String(i === state.week),
                class: "sc-weeks__pill" + (i === state.week ? " is-active" : ""),
                onclick: function () { state.week = i; state.day = firstRide(); render(); },
            }, ["Week " + w.n]);
        }));
    }

    function firstRide() {
        const i = week().days.findIndex((d) => !d.is_rest);
        return i < 0 ? 0 : i;
    }

    function renderSummary() {
        const w = week();
        summaryEl.textContent = w.name + " (" + w.percent + "% volume): " + duration(w.totals.minutes) +
            ", about " + w.totals.km + " km, " + w.totals.rides + " rides. " + w.note;
    }

    function renderList() {
        listEl.replaceChildren.apply(listEl, week().days.map(function (d, i) {
            const spec = data.sessions[d.key];
            const st = statusOf(d);
            const meta = d.is_rest ? "Off the bike" : duration(d.minutes) + " \u00b7 " + d.km + " km";
            return h("button", {
                type: "button", role: "listitem",
                class: "sc-day" + (i === state.day ? " is-active" : "") + (d.is_rest ? " is-rest" : ""),
                "aria-pressed": String(i === state.day),
                onclick: function () { state.day = i; renderList(); renderDetail(); },
            }, [
                h("span", { class: "sc-day__date" }, [d.short]),
                h("span", { class: "sc-day__body" }, [
                    h("span", { class: "sc-day__title" }, [spec.title]),
                    h("span", { class: "sc-day__meta" }, [meta]),
                ]),
                st ? h("span", { class: "sc-badge sc-badge--" + st.cls }, [st.text]) : null,
            ]);
        }));
    }

    function block(title, text) {
        return text ? h("div", { class: "sc-block" }, [h("h4", {}, [title]), h("p", {}, [text])]) : null;
    }

    function panelWorkout(d, spec) {
        if (d.is_rest) return [h("p", { class: "mb-2" }, [spec.summary])].concat(
            spec.steps.map((s) => block(s.label, s.text)));
        return spec.steps.map((s) => block(s.label, s.text)).concat([
            h("p", { class: "sc-note" }, ["Distance is an estimate for your level. Ride by feel, not by speed."]),
        ]);
    }

    function panelRecovery(d, spec) {
        return [h("ul", { class: "sc-list mb-0" }, spec.recovery.map((r) => h("li", {}, [r])))];
    }

    function panelFuel(d) {
        const f = d.fuel;
        return [
            h("p", { class: "sc-stat-line" }, [h("span", {}, ["Carbs today"]), h("strong", {}, [f.daily_carbs])]),
            h("p", { class: "sc-stat-line" }, [h("span", {}, ["Protein today"]), h("strong", {}, [f.daily_protein])]),
            block("Before the ride", f.before), block("During the ride", f.during), block("After the ride", f.after),
            h("div", { class: "sc-block" }, [h("h4", {}, ["Example meals"]),
                h("ul", { class: "sc-list mb-0" }, f.meals.map((m) => h("li", {}, [m])))]),
        ];
    }

    const TABS = [["workout", "Workout"], ["recovery", "Recovery"], ["fuel", "Fuel"]];

    function renderDetail() {
        const d = day();
        const spec = data.sessions[d.key];
        const panels = { workout: panelWorkout, recovery: panelRecovery, fuel: panelFuel };
        const st = statusOf(d);

        const head = h("div", { class: "sc-detail__head" }, [
            h("div", {}, [
                h("p", { class: "sc-eyebrow mb-1" }, [d.label]),
                h("h3", { class: "sc-h2 mb-1" }, [spec.title]),
                h("p", { class: "text-secondary mb-0" }, [spec.summary]),
            ]),
            st ? h("span", { class: "sc-badge sc-badge--" + st.cls }, [st.text]) : null,
        ]);

        const facts = d.is_rest ? null : h("dl", { class: "sc-facts" }, [
            h("div", {}, [h("dt", {}, ["Time"]), h("dd", {}, [duration(d.minutes)])]),
            h("div", {}, [h("dt", {}, ["Distance"]), h("dd", {}, ["~" + d.km + " km"])]),
            h("div", {}, [h("dt", {}, ["Effort"]), h("dd", {}, [h("span", { class: "sc-effort sc-effort--" + spec.effort.toLowerCase().replace(" ", "-") }, [spec.effort])])]),
            h("div", {}, [h("dt", {}, ["RPE"]), h("dd", {}, [spec.rpe + "/10"])]),
        ]);

        const tabs = h("div", { class: "sc-subtabs", role: "tablist" }, TABS.map(function ([key, label]) {
            return h("button", {
                type: "button", role: "tab", "aria-selected": String(state.tab === key),
                class: "sc-subtabs__btn" + (state.tab === key ? " is-active" : ""),
                onclick: function () { state.tab = key; renderDetail(); },
            }, [label]);
        }));

        let action = null;
        const canLog = d.is_past || d.is_today;
        if (!d.is_rest && !d.done && d.log_url) {
            action = canLog
                ? h("a", { class: "btn btn-primary mt-3", href: d.log_url }, ["Log this ride"])
                : h("p", { class: "sc-note" }, ["You can log this ride once the day arrives."]);
        }

        detailEl.replaceChildren.apply(detailEl, [head, facts, tabs]
            .concat(panels[state.tab](d, spec)).concat([action]).filter(Boolean));
    }

    function render() {
        renderPills();
        renderSummary();
        renderList();
        renderDetail();
    }

    render();
})();
