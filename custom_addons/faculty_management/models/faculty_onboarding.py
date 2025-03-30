import secrets
import requests  # For making HTTP requests
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

def onboard_faculty_record(env, faculty):
    """
    Core logic to set a signup token and send an onboarding email
    for a single faculty record.
    """
    if not faculty.email:
        raise ValidationError(_("No email set on faculty record."))

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
    # Use the catchall email or default to a verified sender address.
    email_from = env['ir.config_parameter'].sudo().get_param('mail.catchall.default') or '20eaf4@queensu.ca'

    _send_email(email_from, faculty.email, subject, body_html, env)


def _send_email(email_from, email_to, subject, body_html, env):
    """
    Sends an email using the Mailgun API instead of a local SMTP server.
    """
    # Retrieve Mailgun API key and domain from configuration parameters
    mailgun_api_key = env['ir.config_parameter'].sudo().get_param('mailgun.api_key')
    mailgun_domain = env['ir.config_parameter'].sudo().get_param('mailgun.domain')
    if not mailgun_api_key or not mailgun_domain:
        raise ValidationError(_("Mailgun API key or domain is not configured."))

    url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
    payload = {
        "from": email_from,
        "to": email_to,
        "subject": subject,
        "html": body_html
    }

    try:
        response = requests.post(url, auth=("api", mailgun_api_key), data=payload, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        result = response.json()
        # Mailgun returns an 'id' in the response if successful.
        if not result.get("id"):
            raise ValidationError(_("Mailgun error: %s") % result)
    except Exception as e:
        error_details = response.text if response is not None else 'No response'
        raise ValidationError(_("Failed to send email via Mailgun: %s. Details: %s") % (e, error_details))


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
