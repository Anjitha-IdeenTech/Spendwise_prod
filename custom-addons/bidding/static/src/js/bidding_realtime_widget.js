odoo.define('bidding.BiddingRealtimeWidget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;

    var BiddingRealtimeWidget = AbstractField.extend({
        template: 'bidding.BiddingRealtimeTemplate',

        init: function () {
            if (this.isInitialized) {
                console.log('BiddingRealtimeWidget already initialized for record:', this.record.res_id);
                return;
            }
            this.isInitialized = true;

            this._super.apply(this, arguments);
            this.biddingChannel = null;
            this.lastUpdateTime = 5000;
            this.updateInterval = 500000; // Minimum time between updates (5 seconds)
            this.isUpdating = false;
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._safelyFetchBiddingData();
            });
        },

        start: function () {
            if (this.isStarted) {
                return;
            }
            this.isStarted = true;

            var self = this;
            this.biddingChannel = 'bidding_' + this.record.res_id;
            this.call('bus_service', 'addChannel', this.biddingChannel);
            this.call('bus_service', 'onNotification', this, this._throttledOnNotification.bind(this));
            this.call('bus_service', 'startPolling');
            setTimeout(() => {
                this._renderBiddingData();
            }, 5000);

            console.log('BiddingRealtimeWidget started for record:', this.record.res_id);
            return this._super();
        },

        _safelyFetchBiddingData: function () {
            var self = this;
            return new Promise(function (resolve, reject) {
                self._rpc({
                    model: 'bidding',
                    method: 'read',
                    args: [[self.record.res_id], ['top_vendor', 'top_vendor_price','status']],
                }).then(function (result) {
                    if (result && result.length > 0) {
                        self.biddingData = result[0];
                        console.log('Fetched bidding data:', self.biddingData);
                    }
                    resolve();
                }).guardedCatch(function (error) {
                    console.error('Error fetching bidding data:', error);
                    reject(error);
                });
            });
        },

        _renderBiddingData: function () {
            if (this.biddingData && this.biddingData.status === 'live') {
                console.log('Rendering bidding data for record:', this.record.res_id);
                this.$el.html(QWeb.render('bidding.BiddingRealtimeTemplate', {
                    top_vendor: this.biddingData.top_vendor[1] || 'N/A',
                    top_vendor_price: this.biddingData.top_vendor_price || 0.0,
                }));
                this._setValue(this.biddingData.top_vendor_price);
            }else {
                this.$el.empty(); // Clear the content if status is not 'live'
            }
        },

        _throttledOnNotification: function (notifications) {
            var self = this;

            if (this.isUpdating) {
                console.log('Update in progress, skipping notification');
                return;
            }

            var currentTime = new Date().getTime();
            if (currentTime - this.lastUpdateTime < this.updateInterval) {
                console.log('Skipping update, too soon. Time since last update:', currentTime - this.lastUpdateTime);
                return;
            }

            _.each(notifications, function (notification) {
                if (notification[0] === self.biddingChannel) {
                    console.log('Processing notification for record:', self.record.res_id);
                    self.isUpdating = true;

                    self._safelyFetchBiddingData().then(function () {
                        self._renderBiddingData();
                        self.lastUpdateTime = new Date().getTime();
                    }).finally(function () {
                        self.isUpdating = false;
                    });
                }
            });
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
            if (this.biddingChannel) {
                this.call('bus_service', 'deleteChannel', this.biddingChannel);
            }
            console.log('BiddingRealtimeWidget destroyed for record:', this.record.res_id);
            this.isStarted = false;
            this.isInitialized = false;
            this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('bidding_realtime', BiddingRealtimeWidget);
    return BiddingRealtimeWidget;
});