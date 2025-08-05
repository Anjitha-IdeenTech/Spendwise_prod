odoo.define('product_purchase.custom_script', function (require) {
    "use strict";

    var FormView = require('web.FormView');

    FormView.include({
        render_buttons: function() {
            this._super.apply(this, arguments);
            var self = this;
            if (this.$buttons) {
                this.$buttons.find('.your-custom-button').click(function() {
                    // Call your custom JavaScript function here
                    self.callCustomFunction();
                });
            }
        },

        callCustomFunction: function() {
            // Your custom JavaScript code here
            alert('Hello from custom function!');
        },
    });
});
