{
    "name": "Fitness Membership Dashboard",
    "summary": "Membership KPI dashboard for fitness operations",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-fitness",
    "maintainer": ["SANTZ IT"],
    "maintainer_email": "contato@santzit.com",
    "category": "Association/Fitness",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "fitness_membership",
        "fitness_workout",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fitness_membership_dashboard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
