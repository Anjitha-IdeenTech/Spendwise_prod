odoo.define('bidding.BidRequestTemplateLoader', function (require) {
    "use strict";

    var core = require('web.core');
    var qweb = core.qweb;

    qweb.add_template('/bidding/static/src/xml/bid_request_templates.xml');
});