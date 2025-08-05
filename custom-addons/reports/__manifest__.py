{''
 'name': 'Report Module',
 'summary': """Custom for ERP""",
 'version': '0.1',
 'sequence':'-999999',
 'description': """Lease/Rental Management System""",
 'author': 'Ideenkreise Tech Pvt Ltd',
 'company': 'Ideenkreise Tech Pvt Ltd',
 'website': 'https://www.ideenkreisetech.com',
 'category': 'Tools',
  'depends': ['account','sale','purchase','stock','product_purchase','base','lease_management'],
 'license': 'AGPL-3',
 'data': [
    'report/contract_request.xml',
  'report/report.xml',
  'report/lease_agreement.xml',
  'report/contract.xml',
  'report/po.xml',
  'report/pr.xml',
  'report/bidding.xml',
  'report/invoice.xml',
  'views/view.xml',



 ],
 'demo': [],
 'installable': True,
 'auto_install': False,
 'application' : True
 }
