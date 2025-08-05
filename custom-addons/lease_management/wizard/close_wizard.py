from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, MissingError, UserError
import base64
import io
try:
    import xlrd
except ImportError:
    xlrd = None

class ClosePOWizard(models.TransientModel):
    _name = 'close.po.wizard'
    _description = 'Close Purchase Orders Wizard'

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        string="Purchase Orders",
        domain="[('state', 'in', ('purchase', 'done'))]"
    )
    attachment_file = fields.Binary("Attachment File")
    attachment_filename = fields.Char("Filename", required=True)
    close_reason = fields.Text("Reason for Closing", required=True)

    po_load_message = fields.Text("Load Status", readonly=True, help="Status of the Excel file processing.")


    def load_purchase_orders_from_file(self):
        if not xlrd:
            raise UserError(_("The 'xlrd' library is not installed. Please contact your administrator to install it."))

        if not self.attachment_file:
            raise UserError(_("Please upload an Excel file."))

        try:
            data = base64.b64decode(self.attachment_file)
            workbook = xlrd.open_workbook(file_contents=data)
            sheet = workbook.sheet_by_index(0)

            # Find 'PO Number' column
            header = sheet.row_values(0)
            try:
                po_col_index = header.index('PO Number')
            except ValueError:
                raise UserError(_("Excel file must have a column named 'PO Number'."))

            # Read PO numbers
            po_numbers = []
            for row_idx in range(1, sheet.nrows):
                cell_value = sheet.cell_value(row_idx, po_col_index)
                if cell_value:
                    po_numbers.append(str(cell_value).strip())

            if not po_numbers:
                raise UserError(_("No valid PO numbers found in the Excel file."))

            # Find matching PO records
            chunk_size = 1000
            matching_pos = self.env['purchase.order']
            unmatched_pos = []

            for i in range(0, len(po_numbers), chunk_size):
                chunk = po_numbers[i:i + chunk_size]
                pos = self.env['purchase.order'].search([
                    ('name', 'in', chunk),
                    ('state', 'in', ['purchase', 'done'])
                ])
                matching_pos |= pos
                unmatched_pos.extend([po for po in chunk if po not in pos.mapped('name')])

            if not matching_pos:
                raise UserError(_("No matching purchase orders found in 'purchase' or 'done' state."))

            self.purchase_order_ids = [(6, 0, matching_pos.ids)]

            # Feedback
            message = _(
                "Loaded %d purchase orders successfully.\n"
                "Unmatched PO numbers (%d): %s"
            ) % (
                len(matching_pos),
                len(unmatched_pos),
                ", ".join(unmatched_pos[:10]) + ("..." if len(unmatched_pos) > 10 else "")
            )
            self.po_load_message = message

        except Exception as e:
            raise UserError(_("Error processing Excel file: %s") % str(e))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'close.po.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'name': _('Close Purchase Orders'),
        }
    def action_close_all(self):
        print("i am here",self.purchase_order_ids)
        self.ensure_one()  # Ensure single wizard instance
        if not self.purchase_order_ids:
            raise models.UserError(_("No purchase orders selected."))

        for po in self.purchase_order_ids:
            # Create attachment
            attachment = self.env['ir.attachment'].sudo().create({
                'name': self.attachment_filename or f"PO_{po.name}_closure_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                'datas': self.attachment_file,
                'res_model': 'purchase.order',
                'res_id': po.id,
                'type': 'binary',
            })

        
            po.message_post(
                body=_(
                    "%s has closed the Purchase Order.<br/><br/><strong>Reason:</strong> %s"
                ) % (self.env.user.name, self.close_reason),
            )

            model = self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')], limit=1)
            pending_action = self.env['pending.actions'].sudo().search(
                [('model', '=', model.id), ('record', '=', po.id), ('status', '=', 'open')], limit=1)
            print("the pending action",pending_action)

            if pending_action:
                print(pending_action.name)
                pending_action.status = 'closed'


            activity_type = self.env['mail.activity.type'].search([('name', '=', 'Pending Purchase Order')], limit=1)
            print("type is", self.env.user.id)

            activity = self.env['mail.activity'].search([
                ('res_model_id', '=', self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id),
                ('res_id', '=', po.id),
                ('activity_type_id', '=', activity_type.id),
            ])

            print("the activity is", activity)

            for act in activity:
                print("hai FOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
                print("the activity is", act.id)
                act.action_feedback(feedback="Activity Declined")

            # Update purchase order state (assuming a custom state or field)
            if hasattr(po, 'closed'):
                po.closed = True
            else:
                po.state = 'cancel'  # Example: change state to 'cancel' or another appropriate state
