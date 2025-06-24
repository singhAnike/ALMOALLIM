{
    "name": "custom_module",
    "summary": """ custom module to add other things""",
    "description": """
        This s the custom module added to add custom code
    """,
    "author": "scidecs",
    "website": "https://www.scidecs.com/en-US/",
    "depends": ['base', 'product', 'stock'],

    "data": [
        "security/ir.model.access.csv",
        "wizard/product_wizard.xml",
    ],

}