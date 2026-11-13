"""Plan follow-up: performance stats, tips and plan-change suggestions.

Pure Python (no Flask, no database). The plan the model assigned is the
baseline. After enough training we compare what the cyclist actually did with
what the plan asked for and, only when the numbers are clear, suggest moving
one level up or down. The rules are deliberately simple so they can be
explained to the cyclist.
"""
from datetime import date, timedelta

from app.services.ml_service import PLAN_LEVELS
from app.services.routine_service import LEVEL_NAMES

# --- When can the plan be reviewed? ---
MIN_DAYS_UP, MIN_RIDES_UP = 14, 4        # moving up needs a solid sample
MIN_DAYS_DOWN, MIN_RIDES_DOWN = 7, 3     # moving down for fatigue should not wait as long
RECENT_DAYS = 14                         # fatigue is judged on the last two weeks

# --- Moving UP: all of these must hold ---
UP_ADHERENCE = 0.85       # share of planned rides actually done
UP_VOLUME = 0.95          # share of planned time actually trained
UP_FATIGUE = 4.5          # average perceived fatigue (1-10) at most
UP_RECENT_FATIGUE = 5.0   # ...and the last 7 days at most

# --- Moving DOWN: any of these ---
DOWN_FATIGUE = 7.0        # average perceived fatigue (1-10) at least
DOWN_CHECKIN_FATIGUE = 70 # average check-in fatigue index (0-100) at least
DOWN_CHECKIN_RECOVERY = 35  # average check-in recovery score (0-100) at most


def _avg(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _r(value, digits=1):
    return None if value is None else round(value, digits)


def _speed(w):
    return w.distance_km / (w.duration_min / 60) if w.duration_min and w.distance_km else None


def evaluate_plan(plan, routine, workouts, checkins, today=None):
    """Return stats, tips, status and an optional level-change suggestion.

    plan: TrainingPlan (start_date, end_date)
    routine: result of routine_service.build_routine
    workouts: Workout rows of this cyclist (any dates; filtered here)
    checkins: InjuryCheckin rows of this cyclist (any dates; filtered here)
    """
    today = today or date.today()
    level = routine['level']
    days_on_plan = (today - plan.start_date).days

    wk = [w for w in workouts if plan.start_date <= w.date <= min(today, plan.end_date - timedelta(days=1))]
    recent_from = today - timedelta(days=RECENT_DAYS)
    wk_recent = [w for w in wk if w.date >= recent_from]
    wk_week = [w for w in wk if w.date >= today - timedelta(days=7)]
    ci = [c for c in checkins if max(recent_from, plan.start_date) <= c.date <= today]

    # --- Planned vs. done (a ride counts when logged on its planned date) ---
    days = [d for week in routine['weeks'] for d in week['days']]
    due = [d for d in days if not d['is_rest'] and d['date'] <= today.isoformat()]
    done = [d for d in due if d['done']]
    planned_min = sum(d['minutes'] for d in due)
    actual_min = sum(w.duration_min or 0 for w in wk)
    adherence = len(done) / len(due) if due else None
    volume = actual_min / planned_min if planned_min else None

    # --- Effort vs. plan on planned ride days ---
    planned_rpe = {d['date']: routine['sessions'][d['key']]['rpe'] for d in due}
    gaps = [w.rpe - planned_rpe[w.date.isoformat()] for w in wk
            if w.rpe is not None and w.date.isoformat() in planned_rpe]
    rpe_gap = _avg(gaps)

    # --- Speed trend: first half of rides vs. second half ---
    speeds = [s for s in (_speed(w) for w in sorted(wk, key=lambda x: x.date)) if s]
    speed_trend = None
    if len(speeds) >= 4:
        half = len(speeds) // 2
        speed_trend = _avg(speeds[half:]) - _avg(speeds[:half])

    fatigue = _avg([w.perceived_fatigue for w in wk_recent])
    recent_fatigue = _avg([w.perceived_fatigue for w in wk_week])
    ci_fatigue = _avg([c.fatigue_index for c in ci])
    ci_recovery = _avg([c.recovery_score for c in ci])

    stats = {
        'rides_done': len(done), 'rides_due': len(due),
        'adherence': _r(adherence * 100, 0) if adherence is not None else None,
        'minutes': actual_min, 'planned_minutes': planned_min,
        'volume': _r(volume * 100, 0) if volume is not None else None,
        'km': _r(sum(w.distance_km or 0 for w in wk)),
        'avg_rpe': _r(_avg([w.rpe for w in wk])),
        'rpe_gap': _r(rpe_gap),
        'avg_fatigue': _r(fatigue),
        'avg_speed': _r(_avg(speeds)),
        'speed_trend': _r(speed_trend),
        'checkins': len(ci),
    }

    # --- Weekly planned vs. actual time (only weeks that have started) ---
    weekly = []
    for week in routine['weeks']:
        start = date.fromisoformat(week['days'][0]['date'])
        if start > today:
            break
        end = start + timedelta(days=len(week['days']) - 1)
        actual = sum(w.duration_min or 0 for w in wk if start <= w.date <= end)
        planned = week['totals']['minutes']
        weekly.append({'n': week['n'], 'name': week['name'], 'planned': planned, 'actual': actual,
                       'pct': min(100, round(100 * actual / planned)) if planned else 0})

    # --- Can we review the plan yet? ---
    can_up = days_on_plan >= MIN_DAYS_UP and len(wk) >= MIN_RIDES_UP
    can_down = days_on_plan >= MIN_DAYS_DOWN and len(wk_recent) >= MIN_RIDES_DOWN

    very_fatigued = (
        (fatigue is not None and fatigue >= DOWN_FATIGUE)
        or (len(ci) >= 2 and ((ci_fatigue is not None and ci_fatigue >= DOWN_CHECKIN_FATIGUE)
                              or (ci_recovery is not None and ci_recovery <= DOWN_CHECKIN_RECOVERY)))
    )
    checkin_ok = not ci or (ci_fatigue <= 60 and ci_recovery >= 50)
    great = (
        adherence is not None and adherence >= UP_ADHERENCE
        and volume is not None and volume >= UP_VOLUME
        and fatigue is not None and fatigue <= UP_FATIGUE
        and (recent_fatigue is None or recent_fatigue <= UP_RECENT_FATIGUE)
        and checkin_ok
    )

    status, suggestion = 'collecting', None
    if can_down and very_fatigued:
        status = 'fatigued'
        if level > 0:
            reason = _fatigue_reason(fatigue, ci_fatigue, ci_recovery, len(ci))
            suggestion = _suggest('down', level, reason)
    elif can_up and great:
        status = 'great'
        if level < 2:
            reason = (f'You completed {stats["adherence"]:.0f}% of your planned rides and '
                      f'{stats["volume"]:.0f}% of the planned time, with low fatigue ({fatigue:.1f}/10).')
            suggestion = _suggest('up', level, reason)
    elif can_up:
        status = 'on_track'

    needed = None
    if status == 'collecting':
        days_left = max(0, MIN_DAYS_UP - days_on_plan)
        rides_left = max(0, MIN_RIDES_UP - len(wk))
        needed = (f'Your plan review opens after {MIN_DAYS_UP} days and {MIN_RIDES_UP} logged rides'
                  f' ({days_left} days and {rides_left} rides to go).')

    return {
        'status': status, 'suggestion': suggestion, 'needed': needed,
        'stats': stats, 'weekly': weekly,
        'tips': _tips(level, status, stats, rpe_gap, ci),
        'days_on_plan': days_on_plan,
    }


def _suggest(direction, level, reason):
    to = level + (1 if direction == 'up' else -1)
    return {'direction': direction, 'to_level': to, 'to_label': PLAN_LEVELS[to],
            'to_name': LEVEL_NAMES[to], 'from_name': LEVEL_NAMES[level], 'reason': reason}


def _fatigue_reason(fatigue, ci_fatigue, ci_recovery, n_checkins):
    parts = []
    if fatigue is not None and fatigue >= DOWN_FATIGUE:
        parts.append(f'your perceived fatigue after rides averages {fatigue:.1f}/10')
    if n_checkins >= 2 and ci_fatigue is not None and ci_fatigue >= DOWN_CHECKIN_FATIGUE:
        parts.append(f'your check-in fatigue averages {ci_fatigue:.0f}/100')
    if n_checkins >= 2 and ci_recovery is not None and ci_recovery <= DOWN_CHECKIN_RECOVERY:
        parts.append(f'your recovery score averages {ci_recovery:.0f}/100')
    return 'Recently ' + ' and '.join(parts) + '.'


def _tips(level, status, stats, rpe_gap, checkins):
    tips = []
    if status == 'fatigued':
        tips.append('Take an easy or rest day now and prioritize sleep before your next hard session.')
        if level == 0:
            tips.append('You are already on the base plan, so there is no lower level: swap hard rides for easy ones this week.')
    if status == 'great':
        tips.append('You are handling the plan well. Keep fueling and sleeping the same way as you progress.')
    if stats['adherence'] is not None and stats['adherence'] < 70:
        tips.append(f'You completed {stats["rides_done"]} of {stats["rides_due"]} planned rides. '
                    'Pick fixed days and times for your rides and protect them.')
    if rpe_gap is not None and rpe_gap >= 1.5:
        tips.append('You are riding harder than planned. Slow down on easy days so the hard days stay hard.')
    elif rpe_gap is not None and rpe_gap <= -1.5 and status != 'fatigued':
        tips.append('Sessions feel easier than planned. Make sure you fully commit to the hard intervals.')
    if stats['avg_fatigue'] is not None and stats['avg_fatigue'] >= 6 and status != 'fatigued':
        tips.append('Fatigue is creeping up. Check your sleep and eat enough carbs around your harder rides.')
    if stats['speed_trend'] is not None and stats['speed_trend'] > 0.3:
        tips.append(f'Your average speed is up {stats["speed_trend"]:.1f} km/h compared with your first rides. Nice progress.')
    if not checkins:
        tips.append('Log a daily check-in so your recovery and sleep can be part of this review.')
    if not tips:
        tips.append('Keep following the plan and logging every ride. Your review gets more accurate with each session.')
    return tips[:4]
