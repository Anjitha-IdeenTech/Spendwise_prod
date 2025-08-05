odoo.define('bidding.bid_request_timer', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var BidRequestTimer = AbstractField.extend({
        template: 'BidRequestTimer',

        start: function () {
            this._super.apply(this, arguments);
            this._updateTimer();
        },

        _updateTimer: function () {
            var self = this;
            var now = moment();
            var deadline = moment(this.recordData.deadline);

            if (this.recordData.status === 'live') {
                if (deadline.isAfter(now)) {
                    var duration = moment.duration(deadline.diff(now));
                    var days = Math.floor(duration.asDays());
                    var hours = duration.hours();
                    var minutes = duration.minutes();
                    var seconds = duration.seconds();

                    var remainingTime = days + "d " +
                        ("0" + hours).slice(-2) + ":" +
                        ("0" + minutes).slice(-2) + ":" +
                        ("0" + seconds).slice(-2);

                    this.$el.text(remainingTime);

                    this.update_price(remainingTime);

                    setTimeout(function () {
                        self._updateTimer();
                    }, 1000);
                } else {
                    this.$el.text("Expired");
                    this._updateStatus('complete');
                }
            } else {
                this.$el.text("");
            }
        },

        _updateStatus: function (newStatus) {
            var self = this;
            rpc.query({
                model: 'bid.request',
                method: 'write',
                args: [[this.res_id], {status: newStatus}],
            }).then(function () {
                self.trigger_up('reload');
            });
        },

        update_price: function(remainingTime) {
            var self = this;
            return this._rpc({
                model: 'bid.request',
                method: 'update_price',
                args: [[this.res_id]],
                kwargs: {
                    remaining_time: remainingTime
                }
            }).then(function() {
                // Handle successful update
                self._fetchData();
            }).guardedCatch(function(error) {
                // Handle error
                console.error('Error updating price:', error);
            });
        },

        _fetchData: function() {
            // Implement this method to fetch updated data after a successful price update
            // This could involve reloading the record or fetching specific fields
            this.trigger_up('reload');
        }
    });

    fieldRegistry.add('bid_request_timer', BidRequestTimer);

    return BidRequestTimer;
});