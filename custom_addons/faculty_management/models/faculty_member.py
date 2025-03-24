from odoo import models, fields, api
from odoo.exceptions import ValidationError
from .faculty_onboarding import onboard_faculty_record
import logging

_logger = logging.getLogger(__name__)

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
    import_note = fields.Char(string="Import Note")

    service_duties = fields.Text(string="Service Duties")
    major_service_duties = fields.Text(string="Major Service Duties")
    current_service = fields.Text(string="Current Service")
    signup_token = fields.Char(string="Signup Token", readonly=True)
    signup_token_expiration = fields.Datetime(string="Signup Token Expiration", readonly=True)
    
    @api.model
    def link_or_create_onboarding(self, signup_vals):
        """
        Called when a signup occurs via an onboarding link or during import.
        If a faculty record exists:
          - If it already has a user, record an import note instead of raising an exception.
          - Otherwise, update the record.
        Otherwise, create a new record.
        """
        email = signup_vals.get('email')
        if not email:
            raise ValidationError("Email is required.")

        faculty = self.search([('email', '=', email)], limit=1)
        if faculty:
            # Instead of stopping the process, update with an import note if a user exists.
            if faculty.user_id:
                faculty.sudo().write({
                    'import_note': "A user account has already been created for this faculty member."
                })
                return faculty
            else:
                faculty.write({
                    'name': signup_vals.get('name', faculty.name),
                    # Update additional fields as needed.
                })
        else:
            # Use super() to avoid recursion and create a new record.
            faculty = super(FacultyMember, self).create({
                'name': signup_vals.get('name'),
                'email': email,
                'employee_id': self.env['ir.sequence'].next_by_code('faculty.member') or 'NEW',
            })
        return faculty

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides record creation during import to:
          1. Process each record individually using link_or_create_onboarding.
          2. Run the onboarding logic if applicable.
          3. Catch exceptions per record, allowing partial failures.
        """
        records = self.env['faculty.member']
        for vals in vals_list:
            try:
                rec = self.link_or_create_onboarding(vals)
            except Exception as e:
                _logger.warning("Record creation failed for email %s: %s", vals.get('email'), e)
                # Optionally: if you want, you could create a dummy record with an import note.
                continue

            records |= rec

            # If the record has an email and is not yet linked to a user, attempt onboarding.
            if rec.email and not rec.user_id:
                try:
                    onboard_faculty_record(self.env, rec)
                except Exception as e:
                    _logger.warning("Onboarding invite failed for [%s, email=%s]: %s", rec.name, rec.email, e)
                    rec.sudo().write({'import_note': str(e)})

        return records

    def update_user_link(self, user_id):
        """
        Link the newly created user record with this faculty member.
        """
        if self.user_id:
            raise ValidationError("Faculty member is already linked to a user.")
        self.write({'user_id': user_id})

    # Ensure user deletion when faculty member is deleted
    def unlink(self):
        for faculty in self:
            if faculty.user_id:
                faculty.user_id.unlink()
        return super(FacultyMember, self).unlink()
