import logging
from flask import current_app, render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email

logger = logging.getLogger(__name__)

def _send_email_with_sendgrid(message: Mail, recipient_email: str):
    """
    A private helper function to handle the actual sending of a SendGrid Mail object.
    """
    api_key = current_app.config.get('SENDGRID_API_KEY')
    if not api_key:
        logger.error("SENDGRID_API_KEY is not configured.")
        raise ValueError("Email service is not configured.")

    try:
        sendgrid_client = SendGridAPIClient(api_key)
        response = sendgrid_client.send(message)
        # Use the recipient_email variable directly for logging
        logger.info(f"Email with subject '{message.subject}' sent to {recipient_email}. Status: {response.status_code}")
    except Exception as e:
        logger.exception(f"Failed to send email with subject '{message.subject}' to {recipient_email}: {e}")
        raise

def send_password_reset_email(recipient_email: str, reset_url: str):
    """Constructs and sends a password reset email."""
    sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')
    from_address_with_name = Email(name='WolexChange', email=sender_email)
    message = Mail(
        from_email=from_address_with_name,
        to_emails=recipient_email,
        subject='Password Reset Request',
        plain_text_content=f'To reset your password, please visit the following link: {reset_url}',
        html_content=render_template('reset_password.html', reset_url=reset_url)
    )
    _send_email_with_sendgrid(message, recipient_email)


def send_verification_email(recipient_email: str, verification_url: str, subject: str, template_path: str):
    """Constructs and sends a generic verification email."""
    sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')
    from_address_with_name = Email(name='WolexChange', email=sender_email)
    message = Mail(
        from_email=from_address_with_name,
        to_emails=recipient_email,
        subject=subject,
        plain_text_content=f'To complete this action, please visit the following link: {verification_url}',
        html_content=render_template(template_path, verification_url=verification_url)
    )
    _send_email_with_sendgrid(message, recipient_email)


def send_contact_form_email(name: str, user_email: str, subject: str, message: str):
    """
    Constructs and sends the contact form submission to the admin.
    """
    # Get the admin email from your app config, with a fallback.
    admin_email = current_app.config.get('ADMIN_EMAIL', 'contact@wolexchange.com')
    
    # Use the app's default sender address.
    sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')
    from_address_with_name = Email(name='WolexChange Contact Form', email=sender_email)
    
    # Create an informative subject line for the admin.
    email_subject = f"New Contact Form Submission: {subject}"
    
    # Create a clean, readable plain text body with the user's submission.
    plain_text_content = f"""
    You have received a new message from the WolexChange contact form.
    
    From: {name}
    Reply-To: {user_email}
    Subject: {subject}
    -----------------------------------

    Message:
    {message}
    """
    
    # Construct the SendGrid Mail object.
    message = Mail(
        from_email=from_address_with_name,
        to_emails=admin_email,
        subject=email_subject,
        plain_text_content=plain_text_content
    )
    
    # You could also add a 'Reply-To' header to make replying easier from your email client.
    message.reply_to = Email(user_email, name)
    
    # Send the email using your existing private helper.
    _send_email_with_sendgrid(message, admin_email)