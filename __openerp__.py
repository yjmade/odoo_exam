# -*- coding: utf-8 -*-
{
    'name': "examin",

    'summary': """
        Examin for test""",

    'description': """
        Long description of module's purpose
    """,

    'author': "yjmade",
    'website': "http://www.yjmade.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        "data/examin.exam.status.xml"
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
