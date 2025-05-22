{
    'name': 'Verts',
    'version': '1.0',
    'summary': 'Interview-Questions',
    'depends': ['base', 'web'],
    'data': [
        'views/views.xml',
        'wizard/resize_wizard.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,

    'assets': {
    'web.assets_backend': [
        # 'web/static/lib/jquery.ui/jquery-ui.js',
        'verts_test/static/src/css/resize_wizard.css',
    ],
}

}
