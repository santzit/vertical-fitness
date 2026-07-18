{
    "name": "Fitness Membership",
    "version": "18.0.2.0.0",
    "category": "Services/Association",
    "summary": "Link members to workout plans",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-fitness",
    "maintainer": ["SANTZ IT"],
    "maintainer_email": "contato@santzit.com",
    "license": "AGPL-3",
    "depends": [
        "membership",
        "fitness_workout",
    ],
    "data": [
        "views/fitness_membership_views.xml",
    ],
    "demo": [
        "demo/fitness_membership_demo.xml",
    ],
    "installable": True,
    "application": False,
}
