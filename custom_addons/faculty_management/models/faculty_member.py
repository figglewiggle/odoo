from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FacultyMember(models.Model):
    _name = "faculty.member"
    _description = "Faculty Member"

    name = fields.Char(string="Full Name", required=True)
    email = fields.Char(string="Email", required=True, unique=True)
    user_id = fields.Many2one('res.users', string="Odoo User", readonly=True)  # Prevent manual change
    employee_id = fields.Char(string="Employee ID", required=True, unique=True)
    years_of_service = fields.Integer(string="Years of Service")
    fte = fields.Float(string="FTE")
    last_academic_leave = fields.Date(string="Last Academic Leave")
    next_eligible_leave = fields.Date(string="Next Eligible Leave")
    negotiated_leave = fields.Text(string="Negotiated Leave")
    grants_held = fields.Text(string="Past Grants Held")
    current_grants = fields.Text(string="Current Grants")
    courses_taught = fields.Text(string="Courses Taught")
    courses_current_year = fields.Text(string="Courses This Year")
    teaching_release = fields.Text(string="Teaching Release")

    past_supervision_ba = fields.Text(string="Past BA Supervision")
    past_supervision_ma = fields.Text(string="Past MA Supervision")
    past_supervision_phd = fields.Text(string="Past PhD Supervision")
    current_supervision = fields.Text(string="Current Supervision")

    service_duties = fields.Text(string="Service Duties")
    major_service_duties = fields.Text(string="Major Service Duties")
    current_service = fields.Text(string="Current Service")

    @api.model
    def create(self, vals):
        """ Automatically create an Odoo user when a faculty member is added """

        faculty_group = self.env.ref('faculty_management.group_faculty_member')

        if 'email' in vals:
            existing_user = self.env['res.users'].search([('login', '=', vals['email'])], limit=1)
            
            if existing_user:
                vals['user_id'] = existing_user.id
                # Ensure existing user is added to the faculty group
                if faculty_group.id not in existing_user.groups_id.ids:
                    existing_user.write({'groups_id': [(4, faculty_group.id)]})
            else:
                user = self.env['res.users'].create({
                    'name': vals.get('name'),
                    'login': vals.get('email'),  # Email is used as login
                    'email': vals.get('email'),
                    'password': vals.get('email'),  # Default password = email
                    'groups_id': [(6, 0, [faculty_group.id])],  # Assign Faculty Group
                })
                vals['user_id'] = user.id
        return super(FacultyMember, self).create(vals)

    # Ensure user deletion when faculty member is deleted
    def unlink(self):
        for faculty in self:
            if faculty.user_id:
                faculty.user_id.unlink()
        return super(FacultyMember, self).unlink()
