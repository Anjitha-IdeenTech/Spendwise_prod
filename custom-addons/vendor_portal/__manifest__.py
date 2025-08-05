{''
 'name': 'Vendor Portal',
 'summary': """Custom for ERP""",
 'version': '0.1',
 'sequence': '-11110',
 'description': """Custom for ERP""",
 'author': 'Ideenkreise Tech Pvt Ltd',
 'company': 'Ideenkreise Tech Pvt Ltd',
 'website': 'https://www.ideenkreisetech.com',
 'category': 'Portal',
 'depends': ['sale', 'base_accounting_kit', 'portal', 'base','website'],
 'license': 'AGPL-3',
 'data': [
     'security/groups.xml',
     'security/ir.model.access.csv',
     'views/view.xml',
     'views/vendor_intake.xml',
     'data/data.xml',

 ],

 'assets':{
     'web.assets_frontend':[
         'vendor_portal/static/src/js/validation.js'

     ]
 },

 'demo': [],
 'installable': True,
 'auto_install': False,
 'application': True
 }
