///** @odoo-module **/
//
//import { WebClient } from '@web/webclient/webclient';
//import { patch } from '@web/core/utils/patch';
//import { useService } from '@web/core/utils/hooks';
//
//// Applying a patch to the WebClient class
//patch(WebClient.prototype, 'custom_title_patch', {
//    setup() {
//        this._super();  // Call the original setup method
//        const title = useService('title');
//        console.log('Setting custom title...');
//        title.setParts({ zopenerp: "Ideenkreise" });  // Set your custom title
//
//         const setFavicon = (iconURL) => {
//            let link = document.querySelector("link[rel='icon']");
//            if (!link) {
//                link = document.createElement('link');
//                link.rel = 'icon';
//                document.head.appendChild(link);
//            }
//            link.href = iconURL;
//            console.log('Favicon URL set to:', iconURL);
//        };
//
//        setFavicon(`/bidding/static/src/img/img.ico?v=${new Date().getTime()}`);
//
//    },
//});
//
