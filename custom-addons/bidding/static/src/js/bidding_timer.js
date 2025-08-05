odoo.define('bidding.timer', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');

    var BiddingTimer = AbstractField.extend({
        template: 'BiddingTimer',

        start: function () {
            this._super.apply(this, arguments);
            this.updateInterval = null;
            this._startTimer();
        },

        destroy: function () {
            this._super.apply(this, arguments);
            this._stopTimer();
        },

        _startTimer: function () {
            var self = this;
            this.updateInterval = setInterval(function () {
                self._updateDisplay();
            }, 1000);
        },

        _stopTimer: function () {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        },

        _updateDisplay: function () {
            var start_date = moment(this.recordData.start_date);
            var deadline = moment(this.recordData.deadline);
            var now = moment();

            if (this.recordData.status === 'live' && deadline.isAfter(now)) {
                // Bidding is live
                this.$el.text("Time remaining: " + this._formatDuration(deadline.diff(now)));
            } else if (start_date.isAfter(now)) {
                // Bidding hasn't started yet
                this.$el.text("Bidding starts in: " + this._formatDuration(start_date.diff(now)));
//                this._stopTimer();
            } else if (deadline.isSameOrBefore(now)) {
                // Bidding has ended
                this.$el.text("Bidding ended");
                this._stopTimer();
                this._callEndBidding();
            } else {
                // Status is not live, and bidding hasn't ended
                this.$el.text("Waiting for bidding to start(Reload the Page)");
                this._stopTimer();
            }
        },

        _formatDuration: function (duration) {
            var d = moment.duration(duration);
            var days = Math.floor(d.asDays());
            var hours = d.hours();
            var minutes = d.minutes();
            var seconds = d.seconds();

            return days + "d " +
                ("0" + hours).slice(-2) + ":" +
                ("0" + minutes).slice(-2) + ":" +
                ("0" + seconds).slice(-2);
        },

        _callEndBidding: function () {
            var self = this;
            this._rpc({
                model: this.model,
                method: 'fields_get',
            }).then(function (fields) {
                if ('vendors' in fields) {
                    // This is the bidding model
                    self._rpc({
                        model: self.model,
                        method: 'end_bidding',
                        args: [[self.res_id]],
                    }).then(function (result) {
                        console.log('Bidding ended function called:', result);
                    }).guardedCatch(function (error) {
                        console.error('Error calling end_bidding function:', error);
                    });
                } else {
                    console.log('Not a bidding model, end_bidding not called');
                }
            }).guardedCatch(function (error) {
                console.error('Error checking model fields:', error);
            });
        }
    });

    fieldRegistry.add('bidding_timer', BiddingTimer);

    return BiddingTimer;
});