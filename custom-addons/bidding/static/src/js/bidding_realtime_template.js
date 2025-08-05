odoo.define('bidding.BiddingRealtimeTemplate', function (require) {
    "use strict";

    var core = require('web.core');
    var qweb = core.qweb;

    qweb.add_template('/bidding/static/src/xml/bidding_templates.xml');
});