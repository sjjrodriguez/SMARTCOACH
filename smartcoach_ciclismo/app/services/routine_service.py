"""Cycling-coach routines: training, rest and nutrition for each plan level.

Pure Python (no Flask, no database). Everything is derived from the plan the
cyclist already has (level + age, weight, weekly hours, resting heart rate), so
no schema change is needed. Completion is derived from logged workouts: a
planned ride counts as done when a workout exists on that calendar date.
"""
from datetime import date, timedelta

from app.services.ml_service import PLAN_DESCRIPTIONS, PLAN_LEVELS

LEVEL_NAMES = {0: 'Beginner', 1: 'Moderate', 2: 'Advanced'}
_LABEL_TO_LEVEL = {label: lvl for lvl, label in PLAN_LEVELS.items()}

# Monday..Sunday session for each level.
WEEK = {
    0: ['rest', 'endurance', 'rest', 'cadence', 'rest', 'long', 'recovery'],
    1: ['rest', 'threshold', 'endurance', 'tempo', 'rest', 'long', 'recovery'],
    2: ['rest', 'vo2', 'endurance', 'vo2_short', 'recovery', 'long', 'endurance'],
}

# Relative duration of each ride; minutes = weekly hours split by these weights.
WEIGHTS = {
    0: {'endurance': 1.0, 'cadence': 0.9, 'long': 1.6, 'recovery': 0.7},
    1: {'threshold': 1.0, 'endurance': 1.1, 'tempo': 1.0, 'long': 2.0, 'recovery': 0.6},
    2: {'vo2': 1.0, 'endurance': 1.3, 'vo2_short': 1.0, 'recovery': 0.6, 'long': 2.6},
}

# Four-week progression: volume factor, name and what to do differently.
WEEKS = [
    (0.85, 'Settle in', 'Start a little under your target volume and focus on smooth, controlled efforts.'),
    (1.00, 'Build', 'Full planned volume. Hit the targets without turning easy days into hard days.'),
    (1.10, 'Peak load', 'Your biggest week. Protect sleep and fuel every ride.'),
    (0.65, 'Recovery week', 'Volume drops so your body can absorb the work. Do one repetition fewer in each interval block.'),
]

# Typical average speed (km/h) by session type, shifted by level.
SPEED = {'recovery': 18, 'endurance': 22, 'cadence': 21, 'long': 23,
         'tempo': 25, 'threshold': 24, 'vo2': 24, 'vo2_short': 24}
LEVEL_SPEED_SHIFT = {0: -3, 1: 0, 2: 3}

# Plain-language effort guide: (label, RPE, how it feels / talk test, used for).
EFFORTS = [
    ('Easy', '1-3', 'Full conversation, you could keep going all day.', 'Recovery spins and base rides'),
    ('Steady', '4', 'Full sentences, breathing a little deeper.', 'Long rides and cadence work'),
    ('Moderate', '5-6', 'Short sentences, you feel the work.', 'Tempo blocks'),
    ('Hard', '7-8', 'A few words at a time, hard but controlled.', 'Threshold intervals'),
    ('Very hard', '9-10', 'No talking. Only for short repetitions.', 'VO2 Max intervals'),
]

SESSIONS = {
    'rest': {
        'title': 'Rest day', 'effort': None, 'rpe': None, 'day_type': 'rest',
        'summary': 'Off the bike so your body can absorb the training.',
        'steps': [('Today', 'No riding. Optional: an easy 10-15 minute walk and gentle mobility '
                            '(hips, hamstrings, calves, lower back).')],
        'recovery': ['Reach your full sleep target tonight.',
                     'Eat protein at every meal and drink to thirst.',
                     'Do not "make up" missed rides today; rest is part of the plan.'],
    },
    'recovery': {
        'title': 'Recovery spin', 'effort': 'Easy', 'rpe': 2, 'day_type': 'easy',
        'summary': 'A very light spin to loosen the legs without adding fatigue.',
        'steps': [('Warm-up', 'None needed. Start easy.'),
                  ('Main set', 'Ride flat roads at a very light effort, cadence 85-95 rpm. You should hold a full conversation.'),
                  ('Cool-down', '5 minutes easy, then stretch calves, quads and hip flexors.')],
        'recovery': ['If your legs still feel heavy after 15 minutes, turn around. Today must stay easy.'],
    },
    'endurance': {
        'title': 'Endurance ride', 'effort': 'Easy', 'rpe': 3, 'day_type': 'easy',
        'summary': 'Aerobic base work: steady, conversational and repeatable.',
        'steps': [
            ('Warm-up', '10 minutes easy, building gradually.'),
            ('Main set', {
                0: 'Steady, conversational effort on mostly flat terrain. Every 20 minutes stand up for 20 seconds and take a drink.',
                1: 'Steady, conversational effort with 3 x 5 minutes at a higher cadence (95-100 rpm) to practice smooth pedaling.',
                2: 'Steady, conversational effort for the whole ride. The second half should feel as easy as the first.',
            }),
            ('Cool-down', '5-10 minutes easy.')],
        'recovery': ['Eat a normal meal with protein within 2 hours.'],
    },
    'cadence': {
        'title': 'Endurance + cadence drills', 'effort': 'Steady', 'rpe': 4, 'day_type': 'easy',
        'summary': 'Easy ride with short drills to build a smooth pedal stroke.',
        'steps': [('Warm-up', '10 minutes easy.'),
                  ('Main set', 'Ride at a conversational effort and add 6 x 1 minute of fast pedaling (100-110 rpm, seated, relaxed upper body), each followed by 2 minutes easy.'),
                  ('Cool-down', '5-10 minutes easy and light stretching.')],
        'recovery': ['If a knee or hip complains during drills, stop them and ride easy.'],
    },
    'tempo': {
        'title': 'Tempo / sweet spot', 'effort': 'Moderate', 'rpe': 6, 'day_type': 'quality',
        'summary': 'Sustained moderate-hard work that raises your cruising speed.',
        'steps': [('Warm-up', '15 minutes progressive, finishing with 2 x 1 minute slightly harder.'),
                  ('Main set', '2 x 15 minutes at a moderate effort (short sentences) at 85-95 rpm, with 5 minutes easy between blocks.'),
                  ('Cool-down', '10 minutes easy.')],
        'recovery': ['Refuel within 60-90 minutes and keep tomorrow easy.'],
    },
    'threshold': {
        'title': 'Threshold intervals', 'effort': 'Hard', 'rpe': 7, 'day_type': 'quality',
        'summary': 'Hard, controlled intervals to raise the effort you can sustain.',
        'steps': [('Warm-up', '15 minutes progressive, then 3 x 30 seconds fast with 30 seconds easy.'),
                  ('Main set', '3 x 8 minutes hard but controlled (a few words at a time), with 4 minutes easy between. Keep the last interval as strong as the first.'),
                  ('Cool-down', '10 minutes easy.')],
        'recovery': ['Refuel within 60-90 minutes. Prioritize sleep tonight.'],
    },
    'vo2': {
        'title': 'VO2 Max intervals', 'effort': 'Very hard', 'rpe': 9, 'day_type': 'quality',
        'summary': 'Your hardest aerobic work: short, explosive and fully recovered.',
        'steps': [('Warm-up', '20 minutes progressive with 3 x 1 minute openers.'),
                  ('Main set', '5 x 4 minutes very hard (RPE 9) with 4 minutes easy between. The first minute can feel easy, so pace it: every repetition should look the same.'),
                  ('Cool-down', '10-15 minutes very easy.')],
        'recovery': ['Refuel within 60 minutes. Sleep is your best recovery tool tonight.'],
    },
    'vo2_short': {
        'title': 'Explosive micro-intervals', 'effort': 'Very hard', 'rpe': 9, 'day_type': 'quality',
        'summary': 'Short, explosive repeats that build power at high intensity.',
        'steps': [('Warm-up', '20 minutes progressive with 3 x 1 minute openers.'),
                  ('Main set', '2 sets of 8 x 30 seconds hard / 30 seconds easy, with 6 minutes easy between sets.'),
                  ('Cool-down', '10-15 minutes very easy.')],
        'recovery': ['If power drops sharply in the second set, stop the intervals and ride easy.'],
    },
    'long': {
        'title': 'Long ride', 'effort': 'Steady', 'rpe': 4, 'day_type': 'long',
        'summary': 'Your key endurance session of the week.',
        'steps': [
            ('Warm-up', 'The first 15 minutes very easy.'),
            ('Main set', {
                0: 'Steady, conversational effort on a flat to rolling route. Start eating and drinking within the first 30 minutes.',
                1: 'Steady effort for most of the ride. If your legs feel good, ride the last 20 minutes a little stronger.',
                2: 'Steady effort with 2 x 20 minutes at a moderate effort in the middle. Practice race-day fueling.',
            }),
            ('Cool-down', '10 minutes easy, then a proper meal.')],
        'recovery': ['Eat a full recovery meal and take the evening easy.',
                     'Expect heavier legs tomorrow; keep the next ride very light.'],
    },
}

DAY_TYPE_LABEL = {'rest': 'Rest day', 'easy': 'Easy ride', 'quality': 'Quality session', 'long': 'Long ride'}
CARBS_PER_KG = {'rest': (3, 4), 'easy': (4, 5), 'quality': (6, 8), 'long': (6, 9)}
PROTEIN_PER_KG = (1.4, 1.8)

MEALS = {
    'rest': ['Breakfast: eggs, whole-grain toast and fruit.',
             'Lunch: rice or potatoes, legumes or chicken, large salad.',
             'Snack: yogurt with fruit and nuts.',
             'Dinner: fish or lean meat, vegetables, a small portion of starch.'],
    'easy': ['Breakfast: oatmeal with banana and milk.',
             'Lunch: rice, beans or chicken, vegetables.',
             'Snack: bread with peanut butter and fruit.',
             'Dinner: pasta or potatoes, eggs or fish, vegetables.'],
    'quality': ['Breakfast: oatmeal or white bread with jam, banana and eggs.',
                'Recovery meal: large portion of rice or pasta with chicken or fish.',
                'Snack: fruit, yogurt or a sandwich.',
                'Dinner: potatoes or rice, protein, vegetables.'],
    'long': ['Breakfast (2-3 h before): big bowl of oats or rice, banana, honey.',
             'On the bike: drink mix, bananas, rice cakes or gels.',
             'Recovery meal: rice or pasta, eggs or chicken, fruit, milk.',
             'Dinner: potatoes or other starch, lean protein, vegetables, a little extra salt.'],
}


def level_from_label(label):
    """Map a stored plan label back to its level (0, 1, 2)."""
    if label in _LABEL_TO_LEVEL:
        return _LABEL_TO_LEVEL[label]
    for lvl, name in LEVEL_NAMES.items():
        if (label or '').startswith(name):
            return lvl
    return 0


def _pick(value, level):
    return value[level] if isinstance(value, dict) else value


def _round5(x):
    return int(5 * round(x / 5))


def _g(per_kg, weight):
    return int(10 * round(per_kg * weight / 10))


def _range_g(lo, hi, weight):
    return f'{_g(lo, weight)}-{_g(hi, weight)} g'


def _fuel(day_type, minutes, weight, level, minor):
    """Per-day nutrition: daily targets plus before / during / after a ride."""
    lo, hi = CARBS_PER_KG[day_type]
    fuel = {
        'daily_carbs': _range_g(lo, hi, weight),
        'daily_protein': _range_g(PROTEIN_PER_KG[0], PROTEIN_PER_KG[1], weight),
        'meals': MEALS[day_type],
        'before': None, 'during': None, 'after': None,
    }
    if day_type == 'rest':
        return fuel

    if minutes < 60:
        fuel['before'] = 'A light snack 30-60 minutes before (banana or toast with honey) if you feel hungry.'
    else:
        fuel['before'] = (f'Meal 2-3 hours before with {_range_g(1, 2, weight)} of carbs, low in fat and fiber '
                          '(oats, rice, bread, banana), plus a glass of water.')

    hours = minutes / 60
    if minutes < 60:
        fuel['during'] = 'Water is enough. Take a bottle and drink to thirst.'
    else:
        top = 90 if (minutes > 150 and level == 2 and not minor) else 60
        low = 30 if minutes <= 150 else 60
        fuel['during'] = (f'{low}-{top} g of carbs per hour (about {int(low * hours)}-{int(top * hours)} g in total) '
                          'plus 400-800 ml of fluid per hour. Start in the first 30 minutes.')

    if day_type in ('quality', 'long'):
        fuel['after'] = (f'Within 60-90 minutes: about {_g(1, weight)} g of carbs and '
                         f'{_g(0.3, weight)} g of protein (rice, pasta, eggs, chicken, milk).')
    else:
        fuel['after'] = 'A normal meal with protein within 2 hours.'
    return fuel


def _guide(plan, level, minor):
    weight = plan.weight_kg
    sleep = {0: '7-8 hours', 1: '7.5-8.5 hours', 2: '8-9 hours'}[level]
    return {
        'efforts': [{'label': l, 'rpe': r, 'feel': f, 'used': u} for l, r, f, u in EFFORTS],
        'sleep': sleep,
        'recovery_rules': [
            f'Sleep {sleep} per night. Sleep matters most before and after quality sessions and long rides.',
            'Never stack two hard sessions back to back. This plan already separates them with easy days.',
            'Keep rest days truly easy: walking and mobility only.',
            'After each ride, spend 5-10 minutes on calves, quads, hamstrings, hip flexors and glutes.',
            'Week 4 is a recovery week. Do not skip it; this is when the fitness settles in.',
        ],
        'warning_signs': [
            'Your resting heart rate (if you track it) is 5 or more bpm above normal for 3 days in a row.',
            'Heavy legs or low motivation lasting more than 2-3 days.',
            'Sleep clearly worse than usual.',
            'Any sharp or joint pain (knees, hips, back) while pedaling.',
        ],
        'warning_action': 'Swap your next session for a recovery spin or a rest day, then log a check-in in Injury Tracking.',
        'nutrition_rows': [
            {'label': DAY_TYPE_LABEL[t],
             'carbs_per_kg': f'{CARBS_PER_KG[t][0]}-{CARBS_PER_KG[t][1]} g/kg',
             'carbs': _range_g(*CARBS_PER_KG[t], weight),
             'protein': _range_g(*PROTEIN_PER_KG, weight)}
            for t in ('rest', 'easy', 'quality', 'long')
        ],
        'during_rows': [
            ('Under 60 minutes', 'Water only.'),
            ('60-150 minutes', '30-60 g of carbs per hour.'),
            ('Over 150 minutes', '60 g per hour' + ('.' if level < 2 or minor else ', up to 90 g per hour once your stomach is trained.')),
        ],
        'nutrition_rules': [
            'Drink 400-800 ml per hour while riding, more in heat. Add electrolytes on rides over 90 minutes.',
            f'Spread protein over 3-4 meals (about {_g(0.3, weight)} g each).',
            'Do not cut carbs around quality sessions and long rides; they are your fuel.',
            'Never try new foods or gels on a hard or long day.',
        ],
        'minor_notice': minor,
    }


def build_routine(plan, logged_dates=(), today=None):
    """Return the full 4-week routine for a TrainingPlan.

    plan: any object with level label, age, weight_kg, weekly_hours,
          start_date, end_date.
    logged_dates: dates on which the cyclist logged a workout.
    """
    today = today or date.today()
    logged = set(logged_dates)
    level = level_from_label(plan.plan_label)
    minor = plan.age < 18
    n_days = max((plan.end_date - plan.start_date).days, 7)

    week_keys = WEEK[level]
    weights = WEIGHTS[level]
    total_weight = sum(weights.get(k, 0) for k in week_keys)
    weekly_minutes = plan.weekly_hours * 60

    sessions, weeks = {}, []
    for w in range((n_days + 6) // 7):
        factor, name, note = WEEKS[min(w, len(WEEKS) - 1)]
        days = []
        for i in range(7 * w, min(7 * w + 7, n_days)):
            d = plan.start_date + timedelta(days=i)
            key = week_keys[d.weekday()]
            spec = SESSIONS[key]
            sessions.setdefault(key, {
                'title': spec['title'], 'effort': spec['effort'], 'rpe': spec['rpe'],
                'summary': spec['summary'],
                'steps': [{'label': lbl, 'text': _pick(txt, level)} for lbl, txt in spec['steps']],
                'recovery': spec['recovery'],
            })
            is_rest = key == 'rest'
            minutes = 0 if is_rest else max(20, _round5(weekly_minutes * factor * weights[key] / total_weight))
            km = 0 if is_rest else round(minutes / 60 * (SPEED[key] + LEVEL_SPEED_SHIFT[level]), 1)
            days.append({
                'date': d.isoformat(),
                'label': f'{d:%a, %b} {d.day}',
                'short': f'{d:%a} {d.day}',
                'key': key, 'is_rest': is_rest,
                'minutes': minutes, 'km': km,
                'fuel': _fuel(spec['day_type'], minutes, plan.weight_kg, level, minor),
                'done': d in logged,
                'is_today': d == today,
                'is_past': d < today,
            })
        rides = [x for x in days if not x['is_rest']]
        weeks.append({
            'n': w + 1, 'name': name, 'note': note, 'percent': round(factor * 100),
            'days': days,
            'totals': {'minutes': sum(x['minutes'] for x in days),
                       'km': round(sum(x['km'] for x in days)),
                       'rides': len(rides)},
        })

    all_rides = [x for wk in weeks for x in wk['days'] if not x['is_rest']]
    due = [x for x in all_rides if x['date'] <= today.isoformat()]
    progress = {'done': sum(1 for x in due if x['done']), 'due': len(due), 'total': len(all_rides)}

    # Open on the week/day that contains today (or the first ride of week 1).
    sel_week, sel_day = 0, next((i for i, x in enumerate(weeks[0]['days']) if not x['is_rest']), 0)
    for wi, wk in enumerate(weeks):
        for di, x in enumerate(wk['days']):
            if x['is_today']:
                sel_week, sel_day = wi, di

    return {
        'level': level, 'level_name': LEVEL_NAMES[level], 'description': PLAN_DESCRIPTIONS[level],
        'weeks': weeks, 'sessions': sessions, 'progress': progress,
        'selected': {'week': sel_week, 'day': sel_day},
        'guide': _guide(plan, level, minor),
    }


def find_day(routine, iso_date):
    """Return the day dict for an ISO date, or None."""
    for wk in routine['weeks']:
        for d in wk['days']:
            if d['date'] == iso_date:
                return d
    return None
