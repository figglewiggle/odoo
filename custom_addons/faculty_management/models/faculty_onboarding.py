# faculty_onboarding.py

import secrets
import smtplib
from dateutil.relativedelta import relativedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

def onboard_faculty_record(env, faculty):
    """
    Core logic to set a signup token and send an onboarding email
    for a single faculty record.
    """
    if not faculty.email:
        raise ValidationError(_("No email set on faculty record."))
    
    # Prevent duplicate invites: if a signup_token already exists, do nothing.
    if faculty.signup_token:
        return

    # Check if a res.users record with that email already exists.
    existing_user = env['res.users'].sudo().search([('login', '=', faculty.email)], limit=1)
    if existing_user:
        raise ValidationError(_("A user with email %s already exists.") % faculty.email)

    # Generate token and expiration (48 hours from now)
    token = secrets.token_urlsafe(32)
    expiration = fields.Datetime.to_string(fields.Datetime.now() + relativedelta(hours=48))
    faculty.sudo().write({
        'signup_token': token,
        'signup_token_expiration': expiration,
    })

    # Build the signup URL (this should match the URL used in your controllers)
    base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')
    signup_url = f"{base_url}/signup?token={token}"

    subject = _("You're invited to join the Faculty Portal")
    body_html = f"""
    <p>Hello {faculty.name},</p>
    <p>You have been invited to join the Faculty Portal. Please click on the link below to complete your registration:</p>
    <p><a href="{signup_url}">Complete Registration</a></p>
    <p>If you did not expect this invitation, please ignore this email.</p>
    """
    email_from = env['ir.config_parameter'].sudo().get_param('mail.catchall.default') or 'noreply@example.com'

    _send_email(email_from, faculty.email, subject, body_html)


def _send_email(email_from, email_to, subject, body_html):
    """
    The shared SMTP logic. 
    Identical to your wizard's _send_email, but as a top-level function.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to

    part = MIMEText(body_html, 'html')
    msg.attach(part)

    try:
        smtp = smtplib.SMTP('localhost', 1025)
        smtp.sendmail(email_from, [email_to], msg.as_string())
        smtp.quit()
    except Exception as e:
        raise ValidationError(_("Failed to send email: %s") % e)


class FacultyOnboarding(models.TransientModel):
    _name = 'faculty.onboarding'
    _description = 'Faculty Onboarding'

    email = fields.Char(string="Email", required=True)
    name = fields.Char(string="Full Name", required=True)

    def action_send_invite(self):
        """Uses the same code but calls 'onboard_faculty_record' for 1 record."""
        if not self.email or not self.name:
            raise ValidationError(_("Email and name are required."))

        # 1) Create or update faculty record
        Faculty = self.env['faculty.member'].sudo()
        faculty = Faculty.link_or_create_onboarding({
            'email': self.email,
            'name': self.name,
        })

        # 2) Reuse the 'onboard_faculty_record' function for this single record
        onboard_faculty_record(self.env, faculty)

        return {'type': 'ir.actions.act_window_close'}
