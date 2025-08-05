{''
 'name': 'Pending Actions',
 'summary': """Custom for ERP""",
 'version': '0.1',
 'sequence':'-9999999',
 'description': """Lease/Rental Management System""",
 'author': 'Ideenkreise Tech Pvt Ltd',
 'company': 'Ideenkreise Tech Pvt Ltd',
 'website': 'https://www.ideenkreisetech.com',
 'category': 'Tools',
 'depends': ['account','sale','purchase','stock','product_purchase','base','lease_management'],
 'license': 'AGPL-3',
 'data': [

  'security/ir.model.access.csv',
  'security/access.xml',
  'data/pending_cron.xml',

  'views/view.xml',


 ],
 'demo': [],
 'installable': True,
 'auto_install': False,
 'application' : True
 }
