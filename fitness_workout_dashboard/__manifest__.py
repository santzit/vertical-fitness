{
    "name": "Fitness Workout Dashboard",
    "summary": "Workout KPI dashboard for fitness operations",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-fitness",
    "maintainer": ["SANTZ IT"],
    "maintainer_email": "contato@santzit.com",
    "category": "Association/Fitness",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "web",
        "spreadsheet_dashboard",
        "fitness_membership",
        "fitness_workout",
    ],
    "data": [
        "data/cleanup_legacy.xml",
        "views/workout_dashboard_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "fitness_workout_dashboard/static/src/js/workout_dashboard.js",
            "fitness_workout_dashboard/static/src/xml/workout_dashboard.xml",
            "fitness_workout_dashboard/static/src/scss/workout_dashboard.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
