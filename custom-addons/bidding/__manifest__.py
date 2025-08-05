{
    'name': 'bidding',
    'version': '1.0.0',
    'category': 'bidding',
    'author': 'ideenkreise',
    'sequence': -100,
    'summary': 'bidding management system',
    'description': """bidding management system""",
    'depends': ['base', 'account', 'hr', 'stock', 'purchase', 'base_accounting_kit', 'product_purchase','web','bus'],
    'data': [
        'security/ir.model.access.csv',


        'wizard/add_to_bidding.xml',
        # 'views/assets.xml',
        'views/tenders_inherit_view.xml',
        'views/bid_request.xml',
        # 'views/assets.xml',

        'views/create_bidding.xml',
        'views/asserts.xml',
        'data/ir_cron_data.xml'
    ],
     'assets': {
        'web.assets_backend': [
            'bidding/static/src/js/bidding_realtime_template.js',
            'bidding/static/src/js/bidding_realtime_widget.js',
            'bidding/static/src/xml/bidding_templates.xml',
            'bidding/static/src/js/bid_request_realtime_template.js',
            'bidding/static/src/js/bid_request_realtime_widget.js',
            'bidding/static/src/xml/bid_request_templates.xml',
            'bidding/static/src/js/bidding_timer.js',
            'bidding/static/src/js/bid_request_timer.js',
            'bidding/static/src/js/title.js',
            'bidding/static/src/img/img.ico',
        ],
        'web.assets_qweb': [
                    'bidding/static/src/xml/bidding_timer.xml',
                    'bidding/static/src/xml/bid_request_timer.xml',
                ],
    },
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
