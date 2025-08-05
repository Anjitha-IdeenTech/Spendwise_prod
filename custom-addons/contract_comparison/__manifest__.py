{''
 'name': 'Contract Comparison',
 'summary': """Custom for ERP""",
 'version': '0.1',
 'sequence':'-999999',
 'description': """Contract Comparison""",
 'author': 'Ideenkreise Tech Pvt Ltd',
 'company': 'Ideenkreise Tech Pvt Ltd',
 'website': 'https://www.ideenkreisetech.com',
 'category': 'Tools',
 'depends': ['account','product_purchase','web_domain_field'],
 'license': 'AGPL-3',
 'data': [


  'security/ir.model.access.csv',
  'views/view.xml',
  # 'views/compare.xml',
  'reports/report.xml',


 ],
 'demo': [],
 'installable': True,
 'auto_install': False,
 'application' : True
 }
