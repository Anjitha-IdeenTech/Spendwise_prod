{
    'name': 'Product Types',
    'version': '1.0.0',
    'category': 'Purchase',
    'author': 'ideenkreise',
    'sequence': -100,
    'summary': 'purchase management system',
    'description': """product purchase management system""",
    'depends': ['stock'],
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'multi_company': True
}
