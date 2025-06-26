{
    "name": "custom_module",
    "summary": """ custom module to add other things""",
    "description": """
        This s the custom module added to add custom code
    """,
    "author": "scidecs",
    "website": "https://www.scidecs.com/en-US/",
    "depends": ['base', 'product', 'stock', 'loyalty'],

    "data": [
        "security/ir.model.access.csv",
        "wizard/product_wizard.xml",
        "views/loyalty_program_view.xml"
    ],

}