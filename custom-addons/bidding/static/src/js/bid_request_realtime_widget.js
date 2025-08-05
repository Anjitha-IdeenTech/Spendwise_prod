odoo.define('bidding.BidRequestRealtimeWidget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;

    var BidRequestRealtimeWidget = AbstractField.extend({
        template: 'bidding.BidRequestRealtimeTemplate',

        init: function () {
            if (this.isInitialized) {
                console.log('BidRequestRealtimeWidget already initialized for record:', this.record.res_id);
                return;
            }
            this.isInitialized = true;

            this._super.apply(this, arguments);
            this.bidRequestChannel = null;
            this.lastUpdateTime = 5000;
            this.updateInterval = 500000; // Minimum time between updates (5 seconds)
            this.isUpdating = false;
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._safelyFetchBidRequestData();
            });
        },

        start: function () {
            if (this.isStarted) {
                return;
            }
            this.isStarted = true;

            var self = this;
            this.bidRequestChannel = 'bid_request_' + this.record.res_id;
            this.call('bus_service', 'addChannel', this.bidRequestChannel);

            this.call('bus_service', 'startPolling');
            setTimeout(() => {
                this._renderBidRequestData();
            }, 5000);
            console.log('BidRequestRealtimeWidget started for record:', this.record.res_id);
            return this._super();
        },

        _safelyFetchBidRequestData: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                self._rpc({
                    model: 'bid.request',
                    method: 'read',
                    args: [[self.record.res_id], ['rank','status']],
                }).then(function (result) {
                    if (result && result.length > 0) {
                        self.bidRequestData = result[0];
                        console.log('Fetched bidding data:', self.bidRequestData);
                    }
                    resolve();
                }).guardedCatch(function (error) {
                    console.error('Error fetching bidding data:', error);
                    reject(error);
                });
            });
        },

        _renderBidRequestData: function () {
            if (this.bidRequestData && this.bidRequestData.status === 'live') {
                console.log('Rendering bidding data for record:', this.record.res_id);
                this.$el.html(QWeb.render('bidding.BidRequestRealtimeTemplate', {
                    rank: this.bidRequestData.rank || 'N/A',
                }));
                this._setValue(this.bidRequestData.rank);
            } else {
                this.$el.empty(); // Clear the content if status is not 'live'
            }
        },

        _setValue: function (value) {
            if (this.value !== value) {
                console.log('Setting new value:', value, 'for record:', this.record.res_id);
                this._super(value);
                this.trigger_up('field_changed', {
                    dataPointID: this.dataPointID,
                    changes: _.object([this.name], [value]),
                });
            } else {
                console.log('Value unchanged, not setting');
            }
        },

        destroy: function () {
            if (this.bidRequestChannel) {
                this.call('bus_service', 'deleteChannel', this.bidRequestChannel);
            }
            console.log('BidRequestRealtimeWidget destroyed for record:', this.record.res_id);
            this.isStarted = false;
            this.isInitialized = false;
            this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('bid_request_realtime', BidRequestRealtimeWidget);
    return BidRequestRealtimeWidget;
});