from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import formatLang

# The portal speaks in labels, Odoo stores keys. Keeping the labels identical to
# the ones the React app renders means the serialiser is a plain dict lookup and
# a request round-trips through the API unchanged.
STATE_SELECTION = [
    ('draft', 'Draft'),
    ('to_approve', 'Pending Approval'),
    ('clarification', 'Needs Clarification'),
    ('sourcing', 'Sourcing'),
    ('approved', 'Approved'),
    ('po_confirmed', 'PO Confirmed'),
    ('rejected', 'Rejected'),
    ('paid', 'Paid'),
    # A request withdrawn before it was ordered. Appended last so every key the
    # portal already knows keeps its meaning and its position in the list the
    # /master-data route serves.
    ('cancelled', 'Cancelled'),
]
URGENCY_SELECTION = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
SOURCING_SELECTION = [('direct', 'Direct'), ('rfq', 'RFQ'), ('auction', 'Auction')]

STATE_BY_LABEL = {label: key for key, label in STATE_SELECTION}
URGENCY_BY_LABEL = {label: key for key, label in URGENCY_SELECTION}
SOURCING_BY_LABEL = {label: key for key, label in SOURCING_SELECTION}

# How the portal renders the two dates. We emit exactly these so the value the
# app sends back on the next save parses into the same record.
DISPLAY_DATETIME_FORMAT = '%B %d, %H:%M'
DISPLAY_DATE_FORMAT = '%b %d, %Y'

_DATETIME_INPUT_FORMATS = (
    DISPLAY_DATETIME_FORMAT, '%b %d, %H:%M',
    '%B %d, %Y %H:%M', '%b %d, %Y %H:%M',
    '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S',
)
_DATE_INPUT_FORMATS = (DISPLAY_DATE_FORMAT, '%B %d, %Y', '%Y-%m-%d', '%d/%m/%Y')


def parse_display_datetime(value):
    """Parse a portal date-time label back into a naive datetime, or ``False``."""
    if isinstance(value, datetime):
        return value
    if not value or not isinstance(value, str):
        return False
    for fmt in _DATETIME_INPUT_FORMATS:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
        # "%B %d, %H:%M" carries no year, and strptime defaults it to 1900.
        return parsed.replace(year=fields.Date.today().year) if parsed.year == 1900 else parsed
    return False


def portal_quantity(value):
    """Read a quantity off the portal, never below one.

    The composer's quantity box is a free number input: emptying it posts a 0,
    and Odoo now refuses a line with no quantity. Clamping here keeps that
    typo from silently costing the employee the whole save, and one unit is
    what the field defaults to anyway. The parser already treats a staged
    quantity the same way.
    """
    try:
        quantity = float(value)
    except (TypeError, ValueError):
        return 1.0
    return quantity if quantity > 0 else 1.0


def portal_price(value):
    """Read a unit price off the portal; a negative one is a typo, not a credit."""
    try:
        price = float(value)
    except (TypeError, ValueError):
        return 0.0
    return price if price >= 0 else 0.0


def parse_display_date(value):
    """Parse a portal date label back into a ``date``, or ``False``."""
    if not value or not isinstance(value, str):
        return False
    for fmt in _DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return False


class SmartspendRequest(models.Model):
    _name = 'smartspend.request'
    _description = 'SmartSpend Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, id desc'
    _check_company_auto = True

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'), index=True)
    active = fields.Boolean(default=True)
    state = fields.Selection(
        STATE_SELECTION, string='Status', default='draft', required=True,
        tracking=True, copy=False)
    user_id = fields.Many2one(
        'res.users', string='Requested by', default=lambda self: self.env.user,
        required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    description = fields.Text(
        string='Description', tracking=True,
        help="What is being asked for, and why. Free text — the portal does not "
             "collect it today, so it is filled in from Odoo.")
    notes = fields.Text(
        string='Internal Notes',
        help="Working notes for the buyer and the approver. Never shown to the requester.")

    # -- Flat summary the portal shows on a request card. Lines are the source
    # -- of truth; these are derived so the two can never drift apart.
    product_name = fields.Char(
        string='Product', compute='_compute_summary', store=True,
        help="First requested product — the label the portal shows on the request card.")
    product_qty = fields.Float(
        string='Total Quantity', compute='_compute_summary', store=True, digits='Product Unit')
    target_price = fields.Monetary(
        string='Target Unit Price', compute='_compute_summary', store=True)
    total_cost = fields.Monetary(
        string='Estimated Cost', compute='_compute_summary', store=True, tracking=True)

    # The portal exchanges labels; Odoo files against records. Both are kept:
    # the Char is the API surface, the Many2one is what reporting and budgets use.
    location = fields.Char(string='Branch / Site', tracking=True)
    department = fields.Char(tracking=True)
    expense_category = fields.Char(string='Expense Category', tracking=True)
    branch_id = fields.Many2one('smartspend.branch', string='Branch', tracking=True,
                                check_company=True, index='btree_not_null')
    department_id = fields.Many2one('smartspend.department', string='Department Record',
                                    tracking=True, check_company=True, index='btree_not_null')
    category_id = fields.Many2one('smartspend.expense.category', string='Expense Category Record',
                                  tracking=True, check_company=True, index='btree_not_null')
    expense_type = fields.Selection(related='category_id.expense_type', string='Expense Type', store=True)
    urgency = fields.Selection(URGENCY_SELECTION, default='medium', required=True, tracking=True)
    sourcing_method = fields.Selection(
        SOURCING_SELECTION, string='Sourcing Method', default='direct', required=True)
    buyer_ref = fields.Char(string='Buyer Code', help="SCM buyer desk that owns the sourcing, e.g. SCM-IT-14.")

    partner_id = fields.Many2one('res.partner', string='Vendor', tracking=True)
    vendor_name = fields.Char(
        string='Vendor Name', help="Vendor as named by the portal, kept even when no Odoo contact matches yet.")
    savings = fields.Monetary(string='Negotiated Savings', tracking=True)

    request_date = fields.Datetime(
        string='Requested On', default=fields.Datetime.now, required=True, tracking=True)
    delivery_date = fields.Date(string='Needed By', tracking=True)

    # -- Who did what, and when. The timeline below reads well but is free text;
    # -- these are the fields reporting and future approval routing filter on.
    submitted_by_id = fields.Many2one(
        'res.users', string='Submitted by', readonly=True, copy=False,
        help="Who last sent this request for approval.")
    submitted_on = fields.Datetime(string='Submitted On', readonly=True, copy=False)
    cancelled_by_id = fields.Many2one(
        'res.users', string='Cancelled by', readonly=True, copy=False)
    cancelled_on = fields.Datetime(string='Cancelled On', readonly=True, copy=False)
    cancel_reason = fields.Text(string='Cancellation Reason', readonly=True, copy=False, tracking=True)
    delegated = fields.Boolean(
        string='Raised on Behalf', compute='_compute_delegated', store=True,
        help="The account that created this record is not the one the request is for.")

    line_ids = fields.One2many('smartspend.request.line', 'request_id', string='Requested Items', copy=True)
    bid_ids = fields.One2many('smartspend.request.bid', 'request_id', string='Vendor Bids', copy=False)
    history_ids = fields.One2many('smartspend.request.history', 'request_id', string='Timeline', copy=False)
    comment_ids = fields.One2many('smartspend.request.comment', 'request_id', string='Clarifications', copy=False)
    document_ids = fields.One2many('smartspend.request.document', 'request_id', string='Documents', copy=False)

    # -- Rate contract ------------------------------------------------------
    contract_id = fields.Many2one(
        'smartspend.contract', string='Rate Contract', tracking=True,
        help="Pre-negotiated agreement covering these items. Set by 'Check Rate Contract'.")
    contract_partner_id = fields.Many2one(related='contract_id.partner_id', string='Contracted Vendor')
    contract_reference = fields.Char(related='contract_id.name', string='Contract Reference')
    has_contract = fields.Boolean(compute='_compute_contract_figures', store=True)
    contract_count = fields.Integer(compute='_compute_contract_figures', store=True)
    contract_value = fields.Monetary(
        string='Value at Contract Rates', compute='_compute_contract_figures', store=True)
    contract_savings = fields.Monetary(
        string='Saving vs Target', compute='_compute_contract_figures', store=True)
    contract_coverage = fields.Float(
        string='Lines Covered (%)', compute='_compute_contract_figures', store=True,
        help="Share of the requested lines priced by the matched rate contract.")
    contract_match_label = fields.Char(
        string='Rates Applied', compute='_compute_contract_match_label',
        help="How much of the matched rate card this request uses. A rate contract "
             "prices a catalogue; a request draws on a slice of it.")

    # -- Budget -------------------------------------------------------------
    budget_id = fields.Many2one(
        'smartspend.budget', string='Budget', compute='_compute_budget',
        help="Narrowest running budget covering this request's department, branch and category.")
    budget_available = fields.Monetary(
        string='Budget Available', compute='_compute_budget',
        help="What is left in that budget once this request's own claim is set aside.")
    budget_breach = fields.Boolean(
        string='Over Budget', compute='_compute_budget',
        help="This request costs more than its budget has left.")

    # -- Cost centre --------------------------------------------------------
    # The reference a later phase reserves budget against. Nothing is posted to
    # it yet: it is filled in from the department so the link already exists.
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Cost Center', check_company=True,
        compute='_compute_analytic_account_id', store=True, readonly=False,
        help="Analytic account this spend belongs to. Defaults to the one held "
             "by the requesting department.")

    # -- Documents ----------------------------------------------------------
    # Standard Odoo storage, so a file dropped on the chatter and one attached
    # from the Documents tab are the same record.
    attachment_ids = fields.One2many(
        'ir.attachment', 'res_id', string='Attached Files',
        domain=[('res_model', '=', 'smartspend.request')])
    attachment_count = fields.Integer(string='Files', compute='_compute_attachment_count')

    # -- Purchase orders ----------------------------------------------------
    purchase_order_ids = fields.One2many(
        'purchase.order', 'smartspend_request_id', string='Purchase Orders')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    purchase_order_live_count = fields.Integer(
        string='Open Orders', compute='_compute_purchase_order_count',
        help="Orders raised for this request that have not been cancelled. The "
             "smart button counts every order ever raised, history included; "
             "this is what decides whether another one may be raised.")

    _name_uniq = models.Constraint(
        'UNIQUE(name, company_id)',
        'A purchase request with this reference already exists.',
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('line_ids.product_name', 'line_ids.product_qty', 'line_ids.price_unit', 'line_ids.subtotal')
    def _compute_summary(self):
        for request in self:
            lines = request.line_ids
            request.product_name = lines[:1].product_name or ''
            request.product_qty = sum(lines.mapped('product_qty'))
            request.target_price = lines[:1].price_unit
            request.total_cost = sum(lines.mapped('subtotal'))

    @api.depends('contract_id', 'contract_id.line_ids.price_unit',
                 'line_ids.product_name', 'line_ids.product_qty', 'line_ids.price_unit',
                 'line_ids.contract_line_id')
    def _compute_contract_figures(self):
        for request in self:
            contract, lines = request.contract_id, request.line_ids
            covered = lines.filtered('contract_line_id')
            # An agreement only counts as this request's when it actually prices
            # something on it — otherwise the smart button would advertise a
            # contract that has nothing to do with these items.
            request.has_contract = bool(contract and covered)
            request.contract_count = 1 if (contract and covered) else 0
            if not contract or not lines:
                request.contract_value = 0.0
                request.contract_savings = 0.0
                request.contract_coverage = 0.0
                continue
            # Uncovered lines still cost their target price, so count them in.
            request.contract_value = sum(
                line.product_qty * (line.contract_price if line.contract_line_id else line.price_unit)
                for line in lines
            )
            request.contract_savings = request.total_cost - request.contract_value
            request.contract_coverage = 100.0 * len(covered) / len(lines)

    @api.depends('contract_id', 'line_ids', 'line_ids.contract_line_id')
    def _compute_contract_match_label(self):
        """How much of *this request* the agreement prices.

        Counted against the request's own items, not the rate card's rates:
        a card holding three rates that price three of four requested items is
        not "3 of 3" — that reads as fully covered while an item is going
        unpriced. This says the same thing as Lines Covered (%) beside it.
        """
        for request in self:
            if not request.contract_id:
                request.contract_match_label = ''
                continue
            priced = len(request.line_ids.filtered('contract_line_id'))
            items = len(request.line_ids)
            request.contract_match_label = _(
                "%(priced)s of %(items)s items priced", priced=priced, items=items)

    @api.depends('department_id', 'branch_id', 'category_id', 'request_date', 'total_cost', 'company_id')
    def _compute_budget(self):
        Budget = self.env['smartspend.budget'].sudo()
        for request in self:
            budget = Budget._match_for_request(request)
            request.budget_id = budget
            if not budget:
                request.budget_available = 0.0
                request.budget_breach = False
                continue
            available = budget._available_excluding(request)
            request.budget_available = available
            request.budget_breach = request.total_cost > available

    @api.depends('create_uid', 'user_id')
    def _compute_delegated(self):
        for request in self:
            request.delegated = bool(
                request.create_uid and request.user_id and request.create_uid != request.user_id)

    @api.depends('department_id', 'department_id.analytic_account_id')
    def _compute_analytic_account_id(self):
        for request in self:
            # Never clear a cost centre somebody set by hand.
            request.analytic_account_id = (
                request.department_id.analytic_account_id or request.analytic_account_id)

    def _compute_attachment_count(self):
        # A requester may read their own attachments but not search them freely.
        counts = dict(self.env['ir.attachment'].sudo()._read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids)],
            ['res_id'], ['__count']))
        for request in self:
            request.attachment_count = counts.get(request.id, 0)

    @api.depends('purchase_order_ids', 'purchase_order_ids.state')
    def _compute_purchase_order_count(self):
        # Requesters may not read purchase.order; the count is theirs to see.
        for request in self.sudo():
            orders = request.purchase_order_ids
            request.purchase_order_count = len(orders)
            request.purchase_order_live_count = len(
                orders.filtered(lambda order: order.state != 'cancel'))

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('request_date', 'delivery_date')
    def _check_request_dates(self):
        for request in self:
            if not request.request_date:
                raise ValidationError(_("%s needs a request date.", request.name))
            if request.delivery_date and request.delivery_date < request.request_date.date():
                raise ValidationError(_(
                    "%(request)s is needed by %(needed)s, which is before it was raised "
                    "on %(raised)s. Pick a date on or after the request date.",
                    request=request.name,
                    needed=fields.Date.to_string(request.delivery_date),
                    raised=fields.Date.to_string(request.request_date.date())))

    @api.constrains('user_id')
    def _check_requester(self):
        # OdooBot is archived by design. A request it raises is a cron, a data
        # load or a shell session — not one filed against somebody who has left.
        root = self.env.ref('base.user_root', raise_if_not_found=False)
        for request in self:
            # Read as superuser: a requester may not read other users' records,
            # and refusing the write for that reason would be misleading.
            requester = request.user_id.sudo()
            if requester == root or requester.active:
                continue
            raise ValidationError(_(
                "%(request)s is filed against %(user)s, whose account is archived.",
                request=request.name, user=requester.name))

    # ``currency_id`` is a non-stored related, so it cannot be watched here —
    # the company it hangs off can, and that is what actually decides it.
    @api.constrains('company_id')
    def _check_company_currency(self):
        for request in self:
            if not request.company_id:
                raise ValidationError(_("%s needs a company.", request.name))
            if not request.currency_id:
                raise ValidationError(_(
                    "%(company)s has no currency, so %(request)s cannot be valued.",
                    company=request.company_id.name, request=request.name))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('smartspend.request') or _('New')
        requests = super().create(vals_list)
        for request in requests:
            if not request.history_ids:
                request._log_history(
                    _("Request Submitted"),
                    _("Raised by %(requester)s (created by %(author)s)",
                      requester=request.user_id.name, author=request.create_uid.name)
                    if request.delegated else _("Raised by %s", request.user_id.name),
                    state_to=request.state)
            if request.contract_id:
                request._log_contract_match()
            else:
                request._autofill_contract()
        return requests

    def write(self, vals):
        res = super().write(vals)
        # Items added after the first save still deserve their agreement.
        if 'line_ids' in vals:
            self._autofill_contract()
        return res

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _log_history(self, title, description=False, when=None, state_from=None, state_to=None):
        """Append one entry to the request timeline the portal renders.

        ``state_from`` / ``state_to`` are the audit half of the entry: the
        portal only ever shows the title, the date and the note, but a reviewer
        in Odoo can see which transition the entry stands for and who made it.
        """
        self.ensure_one()
        return self.env['smartspend.request.history'].create({
            'request_id': self.id,
            'title': title,
            'description': description or False,
            'event_date': when or fields.Datetime.now(),
            'user_id': self.env.user.id,
            'state_from': state_from or False,
            'state_to': state_to or False,
        })

    def _history_commands_from_portal(self, entries):
        """Merge the portal's timeline into the stored one instead of replacing it.

        The portal posts the whole request back on every change, timeline
        included. Overwriting the stored timeline with that copy dropped every
        entry Odoo had written since the browser last read the request, so the
        audit trail was only ever as good as the last refresh. Entries are
        merged in now: what Odoo already holds stays, and only genuinely new
        ones are appended.
        """
        known = {(entry.title or '', entry.description or '') for entry in self.history_ids}
        commands = []
        for entry in entries:
            title = entry.get('title') or _('Update')
            description = entry.get('desc') or ''
            if (title, description) in known:
                continue
            known.add((title, description))
            commands.append(fields.Command.create({
                'title': title,
                'description': description or False,
                'event_date': parse_display_datetime(entry.get('date')) or fields.Datetime.now(),
            }))
        return commands

    _MASTER_FIELDS = (
        ('branch_id', 'smartspend.branch', 'location'),
        ('department_id', 'smartspend.department', 'department'),
        ('category_id', 'smartspend.expense.category', 'expense_category'),
    )

    def _sync_master_records(self):
        """Reconcile the portal's labels with the master records they name.

        A request arriving from the portal carries names; one typed in Odoo
        carries records. Whichever side is filled in populates the other, so a
        request is always both readable by the portal and reportable in Odoo.
        """
        resolver = self.env['smartspend.master.mixin']
        for request in self:
            for field_name, model_name, label_field in self._MASTER_FIELDS:
                record, label = request[field_name], request[label_field]
                if not record and label:
                    match = resolver._resolve_master_record(
                        model_name, label, company=request.company_id)
                    if match:
                        request[field_name] = match
                elif record and not label:
                    request[label_field] = record.name

    @api.onchange('branch_id', 'department_id', 'category_id')
    def _onchange_master_records(self):
        for request in self:
            for field_name, _model_name, label_field in request._MASTER_FIELDS:
                if request[field_name]:
                    request[label_field] = request[field_name].name

    def _autofill_contract(self):
        """Match a rate contract as soon as a request has items to match on.

        The portal has always done this on every save. A request typed into
        Odoo used to sit with an empty agreement until somebody thought to
        press "Check Rate Contract" — so the rates, the coverage and the
        contracted vendor were all missing from a perfectly ordinary request.
        """
        for request in self:
            if request.contract_id or not request.line_ids:
                continue
            request.action_check_contract()

    def _log_contract_match(self):
        self.ensure_one()
        return self._log_history(
            _("Rate Contract Mapped"),
            _("%(contract)s with %(vendor)s covers this request.",
              contract=self.contract_id.name, vendor=self.contract_id.partner_id.name))

    @api.onchange('line_ids', 'partner_id')
    def _onchange_lines_match_contract(self):
        """Fill the agreement in as the items are typed, before saving.

        Matching only — the timeline entry is written on save, since an
        onchange must not create records.
        """
        for request in self:
            if request.contract_id or not request.line_ids:
                continue
            contract, _covered = self.env['smartspend.contract']._match_for_products(
                request.line_ids.mapped('product_name'), partner=request.partner_id)
            if contract:
                request.contract_id = contract

    def _sync_partner_from_vendor_name(self):
        """Resolve ``vendor_name`` to a contact, so the PO has someone to go to."""
        Partner = self.env['res.partner']
        for request in self:
            name = (request.vendor_name or '').strip()
            if not name or request.partner_id or name.lower() in ('pending sourcing', 'n/a', 'na'):
                continue
            partner = Partner.search([('name', '=ilike', name)], limit=1)
            if not partner:
                partner = Partner.create({'name': name, 'is_company': True, 'supplier_rank': 1})
            request.partner_id = partner

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def _validate_for_submission(self):
        """Everything that has to be true before a request may leave the requester.

        The portal fills all of this in from its own dropdowns, so this is what
        catches a request typed straight into Odoo — and what a future phase
        will lean on before it reserves budget or resolves an approver.
        """
        self.ensure_one()
        if self.state in ('po_confirmed', 'paid'):
            raise UserError(_("%s has already been ordered; it cannot be submitted again.", self.name))
        if not self.line_ids:
            raise UserError(_("Add at least one item before submitting %s.", self.name))

        missing = []
        if not (self.department_id or self.department):
            missing.append(_("Department"))
        if not (self.branch_id or self.location):
            missing.append(_("Branch / Site"))
        if not (self.category_id or self.expense_category):
            missing.append(_("Expense Category"))
        if not self.delivery_date:
            missing.append(_("Needed By date"))
        if missing:
            raise UserError(_(
                "%(request)s is missing: %(fields)s.",
                request=self.name, fields=", ".join(missing)))

        # The line and header constraints already hold for a saved record; run
        # them again so a request built in one transaction is checked here too,
        # where the message can name the item rather than the field.
        for line in self.line_ids:
            if line.product_qty <= 0:
                raise UserError(_("\"%s\" is requested with no quantity.", line.product_name))
            if line.price_unit < 0:
                raise UserError(_("\"%s\" carries a negative unit price.", line.product_name))
            if not line.product_uom_id:
                raise UserError(_("\"%s\" has no unit of measure.", line.product_name))
        return True

    def action_submit(self):
        """Send the request for approval, and stamp who did so and when."""
        for request in self:
            request._validate_for_submission()
            # The totals are stored computes: make sure the value being
            # submitted is the one the lines actually add up to, not a stale
            # cache from earlier in the transaction.
            request.line_ids.flush_recordset()
            request.invalidate_recordset(['total_cost', 'product_qty', 'target_price'])
            previous = request.state
            request.write({
                'state': 'to_approve',
                'submitted_by_id': self.env.user.id,
                'submitted_on': fields.Datetime.now(),
                'cancelled_by_id': False,
                'cancelled_on': False,
            })
            note = _(
                "Submitted by %(user)s · %(count)s line(s) · %(total)s",
                user=self.env.user.name,
                count=len(request.line_ids),
                total=formatLang(self.env, request.total_cost, currency_obj=request.currency_id))
            request._log_history(
                _("Submitted for Approval"), note, state_from=previous, state_to='to_approve')
            request.message_post(body=note)
        return True

    def _apply_cancel(self, reason=None):
        """Withdraw a request without deleting it, and record who did it and why."""
        for request in self:
            if request.state == 'cancelled':
                raise UserError(_("%s is already cancelled.", request.name))
            if request.state in ('po_confirmed', 'paid'):
                raise UserError(_(
                    "%s has already been ordered — cancel its purchase order first.", request.name))
            live_orders = request.sudo().purchase_order_ids.filtered(lambda o: o.state != 'cancel')
            if live_orders:
                raise UserError(_(
                    "%(request)s still has %(orders)s open. Cancel the order first.",
                    request=request.name, orders=", ".join(live_orders.mapped('name'))))

            previous = request.state
            reason = (reason or request.cancel_reason or '').strip()
            request.write({
                'state': 'cancelled',
                'cancelled_by_id': self.env.user.id,
                'cancelled_on': fields.Datetime.now(),
                'cancel_reason': reason or False,
            })
            note = _(
                "Cancelled by %(user)s from %(previous)s%(reason)s",
                user=self.env.user.name,
                previous=dict(STATE_SELECTION).get(previous, previous),
                reason=_(" — %s", reason) if reason else '')
            request._log_history(
                _("Request Cancelled"), note, state_from=previous, state_to='cancelled')
            request.message_post(body=note)
        return True

    def action_cancel(self):
        """Ask for the reason, then cancel. Cancelling is an audit event, not a click."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Purchase Request'),
            'res_model': 'smartspend.request.cancel',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_ids': self.ids},
        }

    def action_request_clarification(self):
        for request in self:
            previous = request.state
            request.state = 'clarification'
            request._log_history(
                _("Info Requested"), _("Approver asked for clarification"),
                state_from=previous, state_to='clarification')
        return True

    def action_approve(self):
        for request in self:
            previous = request.state
            request.state = 'approved'
            request._log_history(
                _("Approved"), _("Approved by %s", self.env.user.name),
                state_from=previous, state_to='approved')
        return True

    def action_reject(self):
        for request in self:
            previous = request.state
            request.state = 'rejected'
            request._log_history(
                _("Rejected"), _("Rejected by %s", self.env.user.name),
                state_from=previous, state_to='rejected')
        return True

    def action_start_sourcing(self):
        for request in self:
            previous = request.state
            request.state = 'sourcing'
            request._log_history(
                _("Sourcing Triggered"),
                _("No active rate contract found. Routed to the SCM buyer.")
                if not request.contract_id else _("Routed to the SCM buyer."),
                state_from=previous, state_to='sourcing')
        return True

    def action_reset_draft(self):
        for request in self:
            previous = request.state
            if previous == 'draft':
                continue
            request.write({
                'state': 'draft',
                'cancelled_by_id': False,
                'cancelled_on': False,
                'cancel_reason': False,
                'submitted_by_id': False,
                'submitted_on': False,
            })
            request._log_history(
                _("Reset to Draft"),
                _("Reopened by %(user)s from %(previous)s",
                  user=self.env.user.name,
                  previous=dict(STATE_SELECTION).get(previous, previous)),
                state_from=previous, state_to='draft')
        return True

    def action_check_contract(self):
        """Match the request against the running rate contracts."""
        for request in self:
            contract, covered = self.env['smartspend.contract']._match_for_products(
                request.line_ids.mapped('product_name'), partner=request.partner_id)
            request.contract_id = contract
            if contract:
                request._log_history(
                    _("Rate Contract Mapped"),
                    _("%(contract)s with %(vendor)s covers %(covered)s of %(total)s lines.",
                      contract=contract.name, vendor=contract.partner_id.name,
                      covered=len(covered), total=len(request.line_ids)))
            else:
                request._log_history(
                    _("No Active Contract Found"),
                    _("No running agreement covers these items — sourcing is required."))
        return True

    def action_apply_contract_rates(self):
        """Reprice the covered lines at their contracted rate."""
        for request in self:
            if not request.contract_id:
                raise UserError(_("%s has no matched rate contract to apply.", request.name))
            repriced = 0
            for line in request.line_ids.filtered('contract_line_id'):
                if line.price_unit != line.contract_price:
                    line.price_unit = line.contract_price
                    repriced += 1
            if not request.partner_id:
                request.partner_id = request.contract_id.partner_id
                request.vendor_name = request.contract_id.partner_id.name
            request._log_history(
                _("Contract Rates Applied"),
                _("%(count)s line(s) repriced at the %(contract)s rate card.",
                  count=repriced, contract=request.contract_id.name))
        return True

    # ------------------------------------------------------------------
    # Purchase order
    # ------------------------------------------------------------------
    def _prepare_purchase_order_vals(self, partner):
        self.ensure_one()
        return {
            'partner_id': partner.id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'date_order': fields.Datetime.now(),
            'smartspend_request_id': self.id,
            'smartspend_contract_id': self.contract_id.id or False,
        }

    def action_create_purchase_order(self):
        """Turn the request into a draft purchase order (RFQ).

        Lines covered by the matched rate contract are priced at the contracted
        rate; the rest keep the requested target price.
        """
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("%s has no items to order.", self.name))
        # A cancelled order is spent history, not a commitment: it must not
        # stand in the way of raising a replacement. A live one still does.
        live = self.sudo().purchase_order_ids.filtered(lambda order: order.state != 'cancel')
        if live:
            raise UserError(_(
                "%(request)s already has %(orders)s open. Cancel it before raising another.",
                request=self.name, orders=", ".join(live.mapped('name'))))

        self._sync_partner_from_vendor_name()
        partner = self.partner_id or self.contract_id.partner_id
        if not partner:
            raise UserError(
                _("Set a vendor on %s (or match a rate contract) before creating a purchase order.", self.name))

        order = self.env['purchase.order'].create(self._prepare_purchase_order_vals(partner))
        for line in self.line_ids:
            order.order_line = [(0, 0, line._prepare_purchase_order_line_vals(order))]

        # Sourcing is over once the order exists: stop showing the request as
        # "Pending Sourcing" in the portal when the contract named the vendor.
        if not self.partner_id:
            self.partner_id = partner
        if (self.vendor_name or '').strip().lower() in ('', 'pending sourcing', 'n/a', 'na'):
            self.vendor_name = partner.name

        previous = self.state
        self.state = 'po_confirmed'
        self._log_history(
            _("PO Created: %s", order.name),
            _("Sent to %s", partner.name),
            state_from=previous, state_to='po_confirmed')
        self.message_post(body=_("Purchase order %s created from this request.", order.name))
        return self.action_view_purchase_orders()

    # ------------------------------------------------------------------
    # Smart buttons
    # ------------------------------------------------------------------
    def action_view_purchase_orders(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Orders for %s', self.name),
            'res_model': 'purchase.order',
            'domain': [('smartspend_request_id', '=', self.id)],
            'context': {
                'default_smartspend_request_id': self.id,
                'default_partner_id': self.partner_id.id or False,
                'default_origin': self.name,
            },
        }
        if len(self.purchase_order_ids) == 1:
            action.update(view_mode='form', res_id=self.purchase_order_ids.id)
        else:
            action.update(view_mode='list,form')
        return action

    def action_view_attachments(self):
        """The files filed against this request, wherever they were dropped."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Files on %s', self.name),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    def action_view_contract(self):
        """Open the matched agreement, showing the rates that price this request.

        A rate contract prices a catalogue; a request draws on a slice of it.
        Landing on the whole card read as the request's own items being wrong,
        so the request travels in the context and the agreement opens on a tab
        holding just its rates — with the full card one tab away.
        """
        self.ensure_one()
        if not self.contract_id:
            raise UserError(_("No rate contract is mapped to %s yet.", self.name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('%(contract)s rates for %(request)s',
                      contract=self.contract_id.name, request=self.name),
            'res_model': 'smartspend.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'context': dict(self.env.context, smartspend_request_id=self.id),
        }


    # ------------------------------------------------------------------
    # Portal (REST API) serialisation
    # ------------------------------------------------------------------
    # The React portal exchanges one flat JSON shape, ``RequestItem``. These two
    # methods are the only place that shape is spelled out.
    def _to_portal_dict(self):
        """Serialise the request into the portal's ``RequestItem`` shape."""
        self.ensure_one()
        qty = self.product_qty
        return {
            'id': self.name,
            'productName': self.product_name or '',
            'productQty': int(qty) if float(qty).is_integer() else qty,
            'targetPrice': self.target_price,
            'totalCost': self.total_cost,
            'location': self.location or '',
            'department': self.department or '',
            'expenseCategory': self.expense_category or '',
            'status': dict(STATE_SELECTION).get(self.state, 'Draft'),
            'urgency': dict(URGENCY_SELECTION).get(self.urgency, 'Medium'),
            'createdDate': self.request_date.strftime(DISPLAY_DATETIME_FORMAT) if self.request_date else '',
            'deliveryDate': self.delivery_date.strftime(DISPLAY_DATE_FORMAT) if self.delivery_date else '',
            'buyer': self.buyer_ref or '',
            'vendor': self.vendor_name or self.partner_id.name or '',
            'savings': self.savings,
            'selectedSourcingMethod': dict(SOURCING_SELECTION).get(self.sourcing_method, 'Direct'),
            'attachments': self.document_ids.mapped('name'),
            'lineItems': [{
                'productName': line.product_name,
                'productQty': int(line.product_qty) if float(line.product_qty).is_integer() else line.product_qty,
                'targetPrice': line.price_unit,
            } for line in self.line_ids],
            'history': [{
                'title': entry.title,
                'date': entry.event_date.strftime(DISPLAY_DATETIME_FORMAT) if entry.event_date else '',
                'desc': entry.description or '',
            } for entry in self.history_ids],
            'clarificationComments': [{
                'role': comment.role,
                'text': comment.text,
                'date': comment.comment_date.strftime(DISPLAY_DATETIME_FORMAT) if comment.comment_date else '',
            } for comment in self.comment_ids],
            'vendorBids': [{
                'vendorName': bid.vendor_name,
                'price': bid.price,
                'leadTime': bid.lead_time or '',
                'warranty': bid.warranty or '',
                'status': bid.bid_status or '',
            } for bid in self.bid_ids],
            # Extras the portal ignores today but the backend can already answer.
            'contract': self.contract_id.name if self.has_contract else '',
            'contractVendor': self.contract_id.partner_id.name if self.has_contract else '',
            'contractCoverage': round(self.contract_coverage, 1),
            'purchaseOrders': self.sudo().purchase_order_ids.mapped('name'),
            # A related Selection carries no labels of its own: read them off the
            # category, which is where the field is actually defined.
            'expenseType': dict(
                self.env['smartspend.expense.category']._fields['expense_type'].selection
            ).get(self.expense_type, ''),
            'budgetName': self.budget_id.name or '',
            'budgetAvailable': self.budget_available,
            'budgetBreach': self.budget_breach,
        }

    @api.model
    def _vals_from_portal(self, payload, record=None):
        """Translate one portal ``RequestItem`` into Odoo write values.

        Only the keys actually present in ``payload`` are mapped, so the portal
        can send a partial record without wiping the rest.

        :param record: the request being updated, when there is one. The
            timeline is merged against it rather than replaced — see
            :meth:`_history_commands_from_portal`.
        """
        record = record if record is not None else self.browse()
        vals = {}
        simple = {
            'location': 'location',
            'department': 'department',
            'expenseCategory': 'expense_category',
            'buyer': 'buyer_ref',
            'vendor': 'vendor_name',
            # Not sent by the portal today. Accepted so a later client can fill
            # them in without another change on this side.
            'description': 'description',
            'notes': 'notes',
        }
        for key, field_name in simple.items():
            if key in payload:
                vals[field_name] = payload.get(key) or False
        if 'savings' in payload:
            vals['savings'] = float(payload.get('savings') or 0.0)
        if 'status' in payload and payload['status'] in STATE_BY_LABEL:
            vals['state'] = STATE_BY_LABEL[payload['status']]
        if 'urgency' in payload and payload['urgency'] in URGENCY_BY_LABEL:
            vals['urgency'] = URGENCY_BY_LABEL[payload['urgency']]
        if 'selectedSourcingMethod' in payload and payload['selectedSourcingMethod'] in SOURCING_BY_LABEL:
            vals['sourcing_method'] = SOURCING_BY_LABEL[payload['selectedSourcingMethod']]
        if payload.get('createdDate'):
            requested_on = parse_display_datetime(payload['createdDate'])
            if requested_on:
                vals['request_date'] = requested_on
        if 'deliveryDate' in payload:
            vals['delivery_date'] = parse_display_date(payload.get('deliveryDate'))

        lines = payload.get('lineItems')
        if not lines and payload.get('productName'):
            lines = [{
                'productName': payload['productName'],
                'productQty': payload.get('productQty') or 1,
                'targetPrice': payload.get('targetPrice') or 0.0,
            }]
        if lines is not None:
            vals['line_ids'] = [fields.Command.clear()] + [
                fields.Command.create({
                    'sequence': index * 10,
                    'product_name': line.get('productName') or _('Unnamed item'),
                    'product_qty': portal_quantity(line.get('productQty')),
                    'price_unit': portal_price(line.get('targetPrice')),
                })
                for index, line in enumerate(lines)
            ]

        if payload.get('history') is not None:
            commands = record._history_commands_from_portal(payload['history'])
            if commands:
                vals['history_ids'] = commands
        if payload.get('clarificationComments') is not None:
            vals['comment_ids'] = [fields.Command.clear()] + [
                fields.Command.create({
                    'role': comment.get('role') if comment.get('role') in ('manager', 'employee') else 'manager',
                    'text': comment.get('text') or '',
                    'comment_date': parse_display_datetime(comment.get('date')) or fields.Datetime.now(),
                })
                for comment in payload['clarificationComments'] if comment.get('text')
            ]
        if payload.get('vendorBids') is not None:
            vals['bid_ids'] = [fields.Command.clear()] + [
                fields.Command.create({
                    'vendor_name': bid.get('vendorName') or _('Unknown vendor'),
                    'price': float(bid.get('price') or 0.0),
                    'lead_time': bid.get('leadTime') or False,
                    'warranty': bid.get('warranty') or False,
                    'bid_status': bid.get('status') or False,
                })
                for bid in payload['vendorBids'] if bid.get('vendorName')
            ]
        if payload.get('attachments') is not None:
            vals['document_ids'] = [fields.Command.clear()] + [
                fields.Command.create({'name': name})
                for name in payload['attachments'] if name
            ]
        return vals

    @api.model
    def _upsert_from_portal(self, payload):
        """Create or update the request the portal just saved, and return it."""
        reference = (payload.get('id') or '').strip()
        request = self.search([('name', '=', reference)], limit=1) if reference else self.browse()
        vals = self._vals_from_portal(payload, record=request)
        if request:
            request.write(vals)
        else:
            # A brand-new request: let the sequence own the reference unless the
            # portal invented one that is still free. The search above runs
            # under the caller's record rules, so it can miss a reference that
            # belongs to somebody else's request — check without them, or the
            # create would die on the uniqueness constraint.
            if reference and reference.lower() != 'new' and not self.sudo().with_context(
                    active_test=False).search_count([('name', '=', reference)]):
                vals['name'] = reference
            request = self.create(vals)
        request._sync_master_records()
        request._sync_partner_from_vendor_name()
        if not request.contract_id:
            request.action_check_contract()
        return request


    # ------------------------------------------------------------------
    # Demo data
    # ------------------------------------------------------------------
    # Mirrors the seed set the portal ships with, so a freshly reset backend
    # looks like the walkthrough everyone has already seen.
    _DEMO_REQUESTS = [
        {
            'lineItems': [
                {'productName': 'Dell Latitude 5440 Laptop', 'productQty': 20, 'targetPrice': 70000},
                {'productName': 'USB-C Docking Station', 'productQty': 20, 'targetPrice': 8500},
                {'productName': 'Laptop Backpack', 'productQty': 20, 'targetPrice': 1800},
            ],
            'location': 'Bangalore Office', 'department': 'IT & Infrastructure',
            'expenseCategory': 'IT Hardware & Laptops', 'status': 'Pending Approval',
            'urgency': 'High', 'buyer': 'SCM-IT-14', 'vendor': 'Primus Technologies',
            'savings': 60000, 'selectedSourcingMethod': 'RFQ',
            'attachments': ['hardware_specifications.pdf'],
            'vendorBids': [
                {'vendorName': 'Primus Technologies', 'price': 68000, 'leadTime': '5 Days',
                 'warranty': '3 Years On-Site', 'status': 'Recommended'},
                {'vendorName': 'Apex Systems', 'price': 71000, 'leadTime': '10 Days',
                 'warranty': '1 Year Carry-In', 'status': 'Qualified'},
            ],
        },
        {
            'lineItems': [{'productName': 'Ergonomic Office Chair', 'productQty': 10, 'targetPrice': 8000}],
            'location': 'Kochi Head Office', 'department': 'Facilities',
            'expenseCategory': 'Office Furniture', 'status': 'Approved', 'urgency': 'Medium',
            'buyer': 'SCM-FUR-03', 'vendor': 'Apex Systems', 'savings': 5000,
            'selectedSourcingMethod': 'Direct',
            'vendorBids': [{'vendorName': 'Apex Systems', 'price': 8000, 'leadTime': '3 Days',
                            'warranty': '2 Years', 'status': 'Selected'}],
        },
        {
            'lineItems': [{'productName': '19-Inch Data Server Rack', 'productQty': 2, 'targetPrice': 120000}],
            'location': 'Mumbai Office', 'department': 'IT & Infrastructure',
            'expenseCategory': 'Datacenter Equipment', 'status': 'Sourcing', 'urgency': 'High',
            'buyer': 'SCM-IT-14', 'vendor': 'Pending Sourcing', 'savings': 0,
            'selectedSourcingMethod': 'RFQ',
            'vendorBids': [{'vendorName': 'Primus Technologies', 'price': 125000, 'leadTime': '7 Days',
                            'warranty': '3 Years', 'status': 'Submitted'}],
        },
        {
            'lineItems': [{'productName': 'Industrial UPS Unit', 'productQty': 4, 'targetPrice': 85000}],
            'location': 'Mumbai Office', 'department': 'Operations',
            'expenseCategory': 'Datacenter Equipment', 'status': 'Pending Approval', 'urgency': 'High',
            'buyer': 'SCM-IT-14', 'vendor': 'PowerGrid Solutions', 'savings': 22000,
            'selectedSourcingMethod': 'RFQ', 'attachments': ['ups_specs.pdf'],
            'vendorBids': [
                {'vendorName': 'PowerGrid Solutions', 'price': 83000, 'leadTime': '8 Days',
                 'warranty': '3 Years', 'status': 'Recommended'},
                {'vendorName': 'VoltEdge', 'price': 88000, 'leadTime': '6 Days',
                 'warranty': '2 Years', 'status': 'Qualified'},
            ],
        },
        {
            'lineItems': [{'productName': 'Next-Gen Firewall Appliance', 'productQty': 3, 'targetPrice': 145000}],
            'location': 'Bangalore Office', 'department': 'IT & Infrastructure',
            'expenseCategory': 'Datacenter Equipment', 'status': 'Needs Clarification',
            'urgency': 'High', 'buyer': 'SCM-IT-14', 'vendor': 'SecureNet', 'savings': 0,
            'selectedSourcingMethod': 'RFQ', 'attachments': ['network_diagram.pdf'],
            'clarificationComments': [{
                'role': 'manager',
                'text': 'Do these replace the existing units or add capacity?',
            }],
            'vendorBids': [{'vendorName': 'SecureNet', 'price': 143000, 'leadTime': '10 Days',
                            'warranty': '3 Years', 'status': 'Submitted'}],
        },
    ]

    @api.model
    def _create_demo_requests(self):
        """Seed the sample requests used by the portal's "reset demo" button."""
        return self.browse().union(*[
            self._upsert_from_portal(dict(payload)) for payload in self._DEMO_REQUESTS
        ])


class SmartspendRequestLine(models.Model):
    _name = 'smartspend.request.line'
    _description = 'SmartSpend Purchase Request Line'
    _order = 'request_id, sequence, id'

    request_id = fields.Many2one(
        'smartspend.request', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    product_name = fields.Char(string='Product', required=True)
    product_id = fields.Many2one('product.product', string='Odoo Product')
    description = fields.Char(
        string='Description',
        help="What is wanted, in the requester's words. Carried onto the purchase "
             "order line when set; otherwise the product name is.")
    product_category_id = fields.Many2one(
        'product.category', string='Product Category',
        compute='_compute_product_category_id', store=True, readonly=False,
        help="Odoo category this item belongs to. Taken from the product, or from "
             "the request's expense category when the product is still free text.")
    product_qty = fields.Float(string='Quantity', default=1.0, required=True, digits='Product Unit')
    product_uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure',
        compute='_compute_product_uom_id', store=True, readonly=False, precompute=True,
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False),
        help="Unit the quantity is expressed in. Follows the product once one is matched.")
    price_unit = fields.Monetary(string='Target Price')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='request_id.currency_id', string='Currency')
    company_id = fields.Many2one(related='request_id.company_id', store=True)
    notes = fields.Text(string='Notes')

    contract_line_id = fields.Many2one(
        'smartspend.contract.line', string='Contract Line',
        compute='_compute_contract_line', store=True,
        help="Line of the matched rate contract that prices this item.")
    contract_price = fields.Monetary(
        string='Contract Rate', related='contract_line_id.price_unit')
    on_contract = fields.Boolean(compute='_compute_contract_line', store=True)

    @api.depends('product_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.product_qty * line.price_unit

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        default = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        for line in self:
            line.product_uom_id = line.product_id.uom_id or line.product_uom_id or default

    @api.depends('product_id', 'request_id.category_id')
    def _compute_product_category_id(self):
        for line in self:
            line.product_category_id = (
                line.product_id.categ_id
                or line.request_id.category_id.product_category_id
                or line.product_category_id)

    # ------------------------------------------------------------------
    # Constraints — Odoo, not the portal, decides what a line may hold.
    # ------------------------------------------------------------------
    @api.constrains('product_qty')
    def _check_product_qty(self):
        for line in self:
            if line.product_qty <= 0:
                raise ValidationError(_(
                    "\"%s\" must be requested in a quantity greater than zero.", line.product_name))

    @api.constrains('price_unit')
    def _check_price_unit(self):
        for line in self:
            if line.price_unit < 0:
                raise ValidationError(_(
                    "\"%s\" cannot carry a negative unit price.", line.product_name))

    @api.constrains('product_uom_id')
    def _check_product_uom(self):
        for line in self:
            if not line.product_uom_id:
                raise ValidationError(_(
                    "\"%s\" needs a unit of measure.", line.product_name))

    @api.depends('product_name', 'request_id.contract_id', 'request_id.contract_id.line_ids.product_name')
    def _compute_contract_line(self):
        for line in self:
            contract = line.request_id.contract_id
            match = contract._line_for_product(line.product_name) if contract else False
            line.contract_line_id = match or False
            line.on_contract = bool(match)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.product_name = line.product_id.display_name
                if not line.price_unit:
                    line.price_unit = line.product_id.standard_price

    def _find_or_create_product(self):
        """Resolve the free-text product label to a storable Odoo product.

        Sourcing a request may be the first time a product is heard of, and a
        buyer is not normally allowed to create one — so the catalogue entry is
        created as superuser rather than blocking the purchase order.
        """
        self.ensure_one()
        if self.product_id:
            return self.product_id
        Product = self.env['product.product'].sudo()
        product = Product.search([('name', '=ilike', self.product_name)], limit=1)
        if not product:
            product = Product.create({
                'name': self.product_name,
                'type': 'consu',
                'purchase_ok': True,
                'list_price': self.price_unit,
                'standard_price': self.price_unit,
            })
        self.product_id = product.id
        return product

    def _prepare_purchase_order_line_vals(self, order):
        self.ensure_one()
        product = self._find_or_create_product()
        price = self.contract_price if self.contract_line_id else self.price_unit
        # Order in the requested unit when the product actually accepts it;
        # a unit the product does not know would not price or receive correctly.
        uom = self.product_uom_id
        if not uom or uom not in (product.uom_id | product.uom_ids):
            uom = product.uom_id
        return {
            'product_id': product.id,
            'name': self.description or self.product_name,
            'product_qty': self.product_qty,
            'product_uom_id': uom.id,
            'price_unit': price,
            'date_planned': (
                fields.Datetime.to_datetime(self.request_id.delivery_date)
                or order.date_order or fields.Datetime.now()
            ),
        }


class SmartspendRequestBid(models.Model):
    _name = 'smartspend.request.bid'
    _description = 'SmartSpend Vendor Bid'
    _order = 'request_id, price, id'

    request_id = fields.Many2one(
        'smartspend.request', required=True, ondelete='cascade', index=True)
    vendor_name = fields.Char(string='Vendor', required=True)
    partner_id = fields.Many2one('res.partner', string='Contact')
    price = fields.Monetary(string='Quoted Unit Price')
    currency_id = fields.Many2one(related='request_id.currency_id', string='Currency')
    lead_time = fields.Char()
    warranty = fields.Char()
    bid_status = fields.Char(
        string='Status', help="Free-text bid state as shown in the portal: Recommended, Qualified, Selected…")


class SmartspendRequestHistory(models.Model):
    """One audited step in a request's life.

    The portal renders this as a courier-style timeline and reads only the
    title, the date and the note. The user and the two states are the audit
    half: they say who moved the request and where from, which the title alone
    never could.
    """
    _name = 'smartspend.request.history'
    _description = 'SmartSpend Request Timeline Entry'
    _order = 'event_date, id'

    request_id = fields.Many2one(
        'smartspend.request', required=True, ondelete='cascade', index=True)
    title = fields.Char(required=True)
    description = fields.Char()
    event_date = fields.Datetime(default=fields.Datetime.now, required=True)
    user_id = fields.Many2one(
        'res.users', string='Done by', default=lambda self: self.env.user, index='btree_not_null')
    state_from = fields.Selection(STATE_SELECTION, string='Previous Status')
    state_to = fields.Selection(STATE_SELECTION, string='New Status')
    company_id = fields.Many2one(related='request_id.company_id', store=True)


class SmartspendRequestComment(models.Model):
    _name = 'smartspend.request.comment'
    _description = 'SmartSpend Clarification Comment'
    _order = 'comment_date, id'

    request_id = fields.Many2one(
        'smartspend.request', required=True, ondelete='cascade', index=True)
    role = fields.Selection(
        [('manager', 'Manager'), ('employee', 'Employee')], required=True, default='manager')
    text = fields.Text(required=True)
    comment_date = fields.Datetime(default=fields.Datetime.now, required=True)


class SmartspendRequestDocument(models.Model):
    _name = 'smartspend.request.document'
    _description = 'SmartSpend Request Document'
    _order = 'request_id, id'

    request_id = fields.Many2one(
        'smartspend.request', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='File Name', required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')
