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
        "spreadsheet_dashboard",
        "fitness_workout",
    ],
    "data": [
        "data/cleanup_legacy.xml",
        "data/dashboard_groups.xml",
        "data/dashboards.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
