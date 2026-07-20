# WGER Demo Data

This directory contains demo data for the `fitness_workout` module. The three core configuration models
(Categories, Muscles, Equipment) are sourced from the **WGER** open-source fitness project.

## Source

- **WGER API**: https://wger.de/api/v2/
- **License**: WGER data is released under the [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) license.
- **Snapshot date**: 2026-07-20

## Demo Files

| File                                 | Model                       | Records | Notes                                                  |
| ------------------------------------ | --------------------------- | ------- | ------------------------------------------------------ |
| `fitness_exercise_category_demo.xml` | `fitness.exercise.category` | 8       | All WGER exercise categories                           |
| `fitness_muscle_demo.xml`            | `fitness.muscle`            | 15      | All WGER muscles (front + back)                        |
| `fitness_equipment_demo.xml`         | `fitness.equipment`         | 11      | All WGER equipment types                               |
| `fitness_exercise_demo.xml`          | `fitness.exercise`          | 18      | Handcrafted demo exercises referencing WGER categories |
| `fitness_workout_plan_demo.xml`      | `fitness.workout.plan`      | 7       | Demo workout plans with full hierarchy                 |

## Load Order

Categories → Muscles → Equipment → Exercises → Plans

This ensures that all Many2one and Many2many references resolve correctly during demo data loading.

## XML ID Convention

WGER records use deterministic XML IDs based on their WGER API numeric IDs:

- `demo_wger_category_<id>` — e.g., `demo_wger_category_11` = "Chest"
- `demo_wger_muscle_<id>` — e.g., `demo_wger_muscle_4` = "Pectoralis major"
- `demo_wger_equipment_<id>` — e.g., `demo_wger_equipment_1` = "Barbell"

## Refreshing from WGER

To update demo data from the latest WGER API:

```bash
# Fetch current data
curl -s "https://wger.de/api/v2/exercisecategory/?format=json&limit=100" > /tmp/wger_categories.json
curl -s "https://wger.de/api/v2/muscle/?format=json&limit=100" > /tmp/wger_muscles.json
curl -s "https://wger.de/api/v2/equipment/?format=json&limit=100" > /tmp/wger_equipment.json
```

Then regenerate the XML files, preserving the `demo_wger_*` XML ID convention. After updating,
recreate the database to apply changes (these files use `noupdate="1"` so upgrades won't apply them).

## Notes

- All three WGER demo files use `noupdate="1"` — they load on fresh install only.
- Exercises in `fitness_exercise_demo.xml` are handcrafted demo data (not from WGER) but reference
  WGER category XML IDs for proper linkage.
- The exercise demo includes a "Cardio" category (`demo_wger_category_15`) used for conditioning exercises.
- Equipment and muscle records are currently not linked to exercises via Many2many fields in the demo data;
  this can be extended as needed.
