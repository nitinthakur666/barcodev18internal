import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def post_init_hook(cr, registry):
    """Make standard Customers/Contacts menus Admin-only WITHOUT relying on fragile XML IDs.

    - Admin group = base.group_system
    - We hide:
        1) Contacts main menu (if present): contacts.menu_contacts
        2) Any menu pointing to an act_window on res.partner with customer context markers
           like search_default_customer / res_partner_search_mode / default_customer_rank
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    admin_group = env.ref("base.group_system")
    admin_group_id = admin_group.id

    def _set_admin_only(menus, reason=""):
        menus = menus.sudo()
        for menu in menus:
            _logger.info("Setting menu '%s' (id=%s) to Admin-only. %s", menu.complete_name, menu.id, reason)
            menu.write({"groups_id": [(6, 0, [admin_group_id])]})

    _logger.info("Post-init: applying Admin-only menu restrictions for Customers/Contacts.")

    # 1) Hide Contacts top menu (common bypass path)
    try:
        contacts_menu = env.ref("contacts.menu_contacts")
        _set_admin_only(contacts_menu, reason="(contacts.menu_contacts)")
    except ValueError:
        _logger.warning("contacts.menu_contacts not found; skipping Contacts root menu restriction.")

    # 2) Hide "Customers" menus by detecting their action context (robust across setups)
    Act = env["ir.actions.act_window"].sudo()
    Menu = env["ir.ui.menu"].sudo()

    actions = Act.search([("res_model", "=", "res.partner")])

    def _is_customer_partner_list_action(action):
        ctx = (action.context or "").strip()
        return (
            "search_default_customer" in ctx
            or "res_partner_search_mode" in ctx
            or "default_customer_rank" in ctx
        )

    customer_actions = actions.filtered(_is_customer_partner_list_action)
    _logger.info("Detected %s res.partner customer-like actions for menu restriction.", len(customer_actions))

    if customer_actions:
        action_refs = [f"ir.actions.act_window,{a.id}" for a in customer_actions]
        menus = Menu.search([("action", "in", action_refs)])
        _logger.info("Found %s menu items linked to those customer-like actions.", len(menus))
        _set_admin_only(menus, reason="(customer-like res.partner actions)")
