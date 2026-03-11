odoo.define('sale_customer_visibility_match.my_customers_buttons', function (require) {
    "use strict";

    const ListController = require('web.ListController');
    const ListView = require('web.ListView');
    const viewRegistry = require('web.view_registry');

    const MyCustomersListController = ListController.extend({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (!this.$buttons) return;

            if (this.$buttons.find('.o_my_customers_match_customer').length) return;

            const $newBtn = this.$buttons.find('button.o_list_button_add');
            if (!$newBtn.length) return;

            const $btn = $('<button type="button" class="btn btn-primary oe_highlight o_my_customers_match_customer" style="margin-left:8px;">Match Customer</button>');
            $btn.on('click', () => {
                this.do_action('sale_customer_visibility_match.action_customer_match_wizard');
            });

            $newBtn.after($btn);
        },
    });

    const MyCustomersListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: MyCustomersListController,
        }),
    });

    viewRegistry.add('my_customers_tree_button', MyCustomersListView);
});
