from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FacultyLeave(models.Model):
    _name = "faculty.leave"
    _description = "Faculty Leave Request"
    _rec_name = "user_id"

    faculty_id = fields.Many2one("faculty.member", string="Faculty Member", required=True, default=lambda self: self.get_current_faculty())
    leave_type = fields.Selection([
        ('sabbatical', 'Sabbatical'), 
        ('medical', 'Medical'), 
        ('personal', 'Personal')
    ], string="Leave Type", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    reason = fields.Text(string="Reason")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default="submitted")
    user_id = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user, readonly=True, ondelete="cascade")

    ## Auto-assign the faculty member based on the logged-in user
    @api.model
    def get_current_faculty(self):
        faculty = self.env['faculty.member'].search([('user_id', '=', self.env.user.id)], limit=1)
        return faculty.id if faculty else None

    ## Prevent faculty from submitting requests on behalf of others
    @api.constrains('faculty_id')
    def check_faculty_ownership(self):
        for record in self:
            if record.faculty_id.user_id != self.env.user:
                raise ValidationError("You can only request leave for yourself.")

    ## Actions to move leave requests through the workflow
    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        if not self.env.user.has_group('faculty_management.group_faculty_admin'):
            raise ValidationError("Only faculty admins can approve leave requests.")
        self.write({'state': 'approved'})

    def action_reject(self):
        if not self.env.user.has_group('faculty_management.group_faculty_admin'):
            raise ValidationError("Only faculty admins can reject leave requests.")
        self.write({'state': 'rejected'})
