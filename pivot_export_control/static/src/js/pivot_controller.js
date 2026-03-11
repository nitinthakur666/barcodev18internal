/** @odoo-module **/

import { PivotController } from "@web/views/pivot/pivot_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

patch(PivotController.prototype, "pivot_export_control.PivotController", {
    /**
     * Override setup to check export permissions
     */
    setup() {
        this._super(...arguments);
        this.notification = useService("notification");
        this.orm = useService("orm");
        
        onMounted(() => {
            this._checkAndToggleDownloadButton();
        });
    },

    /**
     * Check permission and show/hide download button
     */
    async _checkAndToggleDownloadButton() {
        try {
            // Check if user has export permission

            const hasPermission = await this.orm.call(
                "res.users",
                "has_group",
                ["base.group_allow_export"]
            );

            // const hasBaseExport = await this.orm.call(
            //     "res.users",
            //     "has_group",
            //     ["base.group_allow_export"]
            // );

            // const hasCustomExport = await this.orm.call(
            //     "res.users",
            //     "has_group",
            //     ["pivot_export_control.group_pivot_export_control_user"]
            // );

            // const hasPermission = hasBaseExport || hasCustomExport;
            
            // Find the download button and hide/show it
            const downloadButton = document.querySelector('.o_pivot_download');
            if (downloadButton) {
                if (hasPermission) {
                    downloadButton.style.display = '';
                } else {
                    downloadButton.style.display = 'none';
                }
            }
            
            this.canDownload = hasPermission;
        } catch (error) {
            console.error("Error checking export permission:", error);
            this.canDownload = false;
        }
    },

    /**
     * Override onDownloadButtonClicked to prevent download if no permission
     */
    onDownloadButtonClicked() {
        if (!this.canDownload) {
            this.notification.add(
                "You don't have permission to export data. Please contact your administrator.",
                {
                    type: "warning",
                }
            );
            return;
        }
        return this._super(...arguments);
    },
});
