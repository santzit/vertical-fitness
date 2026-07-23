{
    "name": "Fitness Workout Portal",
    "summary": "WGER-style workout portal for members",
    "author": "CSANTZ, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-fitness",
    "category": "Website",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "website",
        "portal",
        "fitness_workout",
    ],
    "data": [
        "security/portal_security.xml",
        "views/portal_templates.xml",
    ],
    "demo": [
        "demo/portal_routines.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "fitness_workout_portal/static/src/scss/portal.scss",
            "fitness_workout_portal/static/src/js/portal_store.js",
            "fitness_workout_portal/static/src/js/portal_app.js",
            "fitness_workout_portal/static/src/xml/*.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
