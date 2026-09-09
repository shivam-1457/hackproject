import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger("uvicorn")

# In-memory store for recent sent emails (useful for testing & development preview)
sent_emails_store: List[Dict[str, Any]] = []

def send_email_message(to_email: str, subject: str, html_body: str, plain_text: str = ""):
    """
    Sends an email using configured SMTP, or logs it to console and dev store
    if SMTP is disabled or unavailable.
    """
    email_record = {
        "to": to_email,
        "subject": subject,
        "html_body": html_body,
        "plain_text": plain_text,
        "timestamp": datetime.utcnow().isoformat()
    }
    sent_emails_store.insert(0, email_record)
    if len(sent_emails_store) > 50:
        sent_emails_store.pop()

    if settings.SMTP_ENABLED and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email

            if plain_text:
                msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            logger.info(f"[Email Sent via SMTP] To: {to_email} | Subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"[SMTP Error] Failed to send email to {to_email}: {e}")
            # Fall back to logged mode
    
    logger.info(f"================== [DEV EMAIL LOG] ==================")
    logger.info(f"TO: {to_email}")
    logger.info(f"SUBJECT: {subject}")
    logger.info(f"CONTENT PREVIEW: {plain_text or subject}")
    logger.info(f"=====================================================")
    return True

def send_verification_email(to_email: str, full_name: str, token: str):
    """
    Sends token-based email verification link to newly registered user.
    """
    verify_url = f"{settings.FRONTEND_URL}/verify-email.html?token={token}"
    subject = "Verify your Kisan2Consumer Account"
    plain_text = f"Hello {full_name},\n\nPlease verify your Kisan2Consumer account using token:\n{token}\n\nOr click here: {verify_url}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff;">
        <div style="background-color: #2e7d32; color: white; padding: 15px; border-radius: 6px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Kisan2Consumer (SIH26033)</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Direct Farm-to-Consumer Agricultural Platform</p>
        </div>
        <div style="padding: 20px 10px;">
            <p style="font-size: 16px; color: #333;">Namaste <strong>{full_name}</strong>,</p>
            <p style="font-size: 15px; color: #555; line-height: 1.5;">
                Welcome to Kisan2Consumer! You have registered to participate in direct, transparent agricultural trade.
                Please verify your email address to activate your account and access the marketplace.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" style="background-color: #2e7d32; color: #ffffff; padding: 12px 25px; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 5px; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px dashed #ccc; font-family: monospace; font-size: 14px; text-align: center;">
                Verification Token: <strong>{token}</strong>
            </div>
            <p style="font-size: 13px; color: #777; margin-top: 25px;">
                If you did not create an account on Kisan2Consumer, you can safely ignore this email.
            </p>
        </div>
        <div style="border-top: 1px solid #eee; padding-top: 15px; text-align: center; font-size: 12px; color: #999;">
            © 2026 Kisan2Consumer • SIH 2026 Problem Statement SIH26033
        </div>
    </div>
    """
    return send_email_message(to_email, subject, html_body, plain_text)

def send_order_confirmation_email(to_email: str, full_name: str, order_id: int, total_amount: float, items_summary: str):
    """
    Sends order confirmation email with bill summary to consumer.
    """
    subject = f"Order #{order_id} Confirmed - Kisan2Consumer"
    plain_text = f"Hello {full_name},\n\nYour order #{order_id} has been confirmed.\nTotal: Rs {total_amount:.2f}\nItems:\n{items_summary}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <div style="background-color: #1b5e20; color: white; padding: 15px; border-radius: 6px; text-align: center;">
            <h2 style="margin: 0;">Order Confirmed! 🌾</h2>
        </div>
        <div style="padding: 20px 10px;">
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Thank you for supporting our local farmers directly! Your order <strong>#{order_id}</strong> is placed and being prepared for harvest & dispatch.</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h4 style="margin-top: 0;">Order Summary</h4>
                <p style="white-space: pre-line; margin: 5px 0;">{items_summary}</p>
                <hr style="border: 0; border-top: 1px solid #ddd; margin: 10px 0;">
                <p style="font-size: 18px; font-weight: bold; color: #2e7d32; margin: 0;">Grand Total: ₹{total_amount:.2f}</p>
            </div>
            <p style="font-size: 14px; color: #666;">You can track your order live from your Consumer Dashboard.</p>
        </div>
    </div>
    """
    return send_email_message(to_email, subject, html_body, plain_text)

def send_farmer_order_alert(farmer_email: str, farmer_name: str, order_id: int, product_title: str, quantity: float, unit: str):
    """
    Sends new order alert email to farmer.
    """
    subject = f"New Order Alert #{order_id} for {product_title}!"
    plain_text = f"Namaste {farmer_name},\n\nYou received a new order #{order_id} for {quantity} {unit} of {product_title}."
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <div style="background-color: #2e7d32; color: white; padding: 15px; border-radius: 6px; text-align: center;">
            <h2 style="margin: 0;">New Produce Order! 🚜</h2>
        </div>
        <div style="padding: 20px 10px;">
            <p>Namaste <strong>{farmer_name}</strong>,</p>
            <p>A consumer has placed a direct order for your produce:</p>
            <ul>
                <li><strong>Order ID:</strong> #{order_id}</li>
                <li><strong>Produce:</strong> {product_title}</li>
                <li><strong>Quantity:</strong> {quantity} {unit}</li>
            </ul>
            <p>Please log in to your Farmer Dashboard to confirm and schedule shipping.</p>
        </div>
        <div style="border-top: 1px solid #eee; padding-top: 15px; text-align: center; font-size: 12px; color: #999;">
            © 2026 Kisan2Consumer Helpdesk (kisan2consumerhelp@gmail.com) • SIH 2026
        </div>
    </div>
    """
    return send_email_message(farmer_email, subject, html_body, plain_text)

def send_dispute_verdict_email(to_email: str, recipient_name: str, complaint_id: int, order_id: int, verdict: str, remarks: str):
    """
    Sends notification to farmer or consumer when an admin resolves a dispute.
    """
    subject = f"Dispute #{complaint_id} Arbitration Decision - Kisan2Consumer"
    plain_text = f"Hello {recipient_name},\n\nAn official verdict has been issued for Dispute #{complaint_id} on Order #{order_id}.\nStatus: {verdict}\nRemarks: {remarks}\n\nQuestions? Contact kisan2consumerhelp@gmail.com"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <div style="background-color: #1e3a8a; color: white; padding: 15px; border-radius: 6px; text-align: center;">
            <h2 style="margin: 0;">Dispute Arbitration Decision ⚖️</h2>
        </div>
        <div style="padding: 20px 10px;">
            <p>Dear <strong>{recipient_name}</strong>,</p>
            <p>The Kisan2Consumer Grievance Desk has reviewed and issued an arbitration decision for <strong>Dispute #{complaint_id}</strong> (Order #{order_id}):</p>
            <div style="background-color: #f8fafc; border-left: 4px solid #1e3a8a; padding: 15px; margin: 15px 0;">
                <p style="margin: 0 0 8px;"><strong>Official Verdict:</strong> <span style="color: #1e3a8a; font-weight: 700;">{verdict}</span></p>
                <p style="margin: 0;"><strong>Arbitrator Remarks:</strong> {remarks}</p>
            </div>
            <p style="font-size: 13px; color: #64748b;">If you have further questions or require assistance, reach out to our grievance officer at <strong>kisan2consumerhelp@gmail.com</strong>.</p>
        </div>
        <div style="border-top: 1px solid #eee; padding-top: 15px; text-align: center; font-size: 12px; color: #999;">
            © 2026 Kisan2Consumer Ombudsman Desk • kisan2consumerhelp@gmail.com
        </div>
    </div>
    """
    return send_email_message(to_email, subject, html_body, plain_text)
