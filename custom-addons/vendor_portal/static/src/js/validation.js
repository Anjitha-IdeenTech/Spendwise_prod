odoo.define("vendor_portal.NewVendorForm" ,function(require){
'use strict';

var publicWidget = require("web.public.widget");
    console.log("helllooooooooooooooooooooo console workingggggggggggggggg");


publicWidget.registry.new_vendor_form_view = publicWidget.Widget.extend({

    selector:"#new_vendor_creation",
    events:{
        'submit':"_onSubmitButton",
    },

    _onSubmitButton:function(evt){
        console.log("helllooooooooooooooooooooo ON SUBMIT CALLED");
        var vendorname = this.$("input[name='name']").val();
        var vendormobile = this.$("input[name='mobile']").val();
        var vendormail = this.$("input[name='mail']").val();
        var vendorgst = this.$("input[name='gst']").val();
        var vendorpan = this.$("input[name='pan']").val();
        var vendorpin = this.$("input[name='pin']").val();
        var vendorbank_acc = this.$("input[name='bank_acc']").val();
        var vendortel = this.$("input[name='tel']").val();

        var $vendorstate = this.$("select[name='state_id']");
        var vendor_state = ($vendorstate.val() || '0');

        var $vendor_product_category = this.$("select[name='pdt_category']");
        var vendor_product_category = ($vendor_product_category.val() || '0');


        if (!vendor_product_category || vendor_product_category==0) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please select vendor category");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

        if (!vendor_product_category.match(/^[0-9]+$/) ) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please select proper vendor category");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }


        if (!vendor_state || vendor_state==0) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please select state");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

        if (!vendor_state.match(/^[0-9]+$/) ) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please select proper state");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

        if(!vendorname){
            console.log("CONDITIONNNNNNNNNNNN CALLED");
            $('#vendor_client_side_validation').html("Please enter a name");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }
        if(!vendormobile.match(/^\d{10}$/)) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please valid a mobile no");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

        if (!vendormail.match(/^[\w-]+(\.[\w-]+)*@([\w-]+\.)+[a-zA-Z]{2,7}$/)) {
            console.log("CONDITIONNNNNNNNNNNN 4 CALLED");
            $('#vendor_client_side_validation').html("Please enter a valid email address");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

       /* if (!vendorgst.match(/^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z\d{1}$/)) {
            console.log("CONDITIONNNNNNNNNNNN 5 CALLED");
            $('#vendor_client_side_validation').html("Please enter a valid GST number");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        } */

        if (!vendorpan.match(/^([A-Z]){5}([0-9]){4}([A-Z]){1}$/)) {
            console.log("CONDITIONNNNNNNNNNNN 6 CALLED");
            $('#vendor_client_side_validation').html("Please enter a valid PAN number");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

        if (!vendorpin.match(/^\d{6}$/)) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please enter a valid 6-digit PIN code");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }

       /* if (!vendorbank_acc.match(/^\d{8,18}$/)) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please enter a valid bank account number");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        } */

        /*if (!vendortel.match(/^\d+$/)) {
            console.log("CONDITIONNNNNNNNNNNN 3 CALLED");
            $('#vendor_client_side_validation').html("Please enter a telephone valid number");
            $('#vendor_client_side_validation').show();
            evt.preventDefault();
        }*/












    },


});
});
