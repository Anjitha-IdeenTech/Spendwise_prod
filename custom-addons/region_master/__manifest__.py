{
    'name': 'Region Master',
    'version': '1.0.0',
    'category': 'Region Master',
    'author': 'ideenkreise',
    'sequence': -100,
    'summary': 'Region Selection',
    'description': """Region Master m system""",
    'depends': ['base', 'account', 'hr', 'stock', 'purchase', 'base_accounting_kit', 'web_domain_field'],
    'data': [

        'security/ir.model.access.csv',
        'views/vendor_pr_limit.xml',
        'views/division_masters.xml',
        'views/subdivision_masters.xml',
        'views/region_masters.xml',
        'views/branch_inherit.xml',


    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'multi_company': True
}
