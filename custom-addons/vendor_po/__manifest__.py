{''
 'name': 'Vendor Purchase Order',
 'summary': """Custom for ERP""",
 'version': '0.1',
 'sequence': '-11111',
 'description': """Custom for ERP""",
 'author': 'Ideenkreise Tech Pvt Ltd',
 'company': 'Ideenkreise Tech Pvt Ltd',
 'website': 'https://www.ideenkreisetech.com',
 'category': 'Tools',
 'depends': ['sale', 'base_accounting_kit', 'purchase', 'base', 'stock', 'vendor_portal'],
 'license': 'AGPL-3',
 'data': [
     # 'security/groups.xml',
     'security/ir.model.access.csv',
    'views/account_move_inherit.xml',
     'views/view.xml',
     'views/deliver_date.xml',
     'views/invoice_view.xml',
     'views/asn.xml',
     # 'views/vendor_intake.xml',
     'data/data.xml',

 ],

 'demo': [],
 'installable': True,
 'auto_install': False,
 'application': True
 }
