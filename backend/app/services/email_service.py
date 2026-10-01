import smtplib
import re
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import EmailStr, TypeAdapter
from app.core.config import settings
from app.core.logging import logger
from app.models.patient import Patient
from app.models.report import Report


class EmailDeliveryError(Exception):
    """Custom exception raised when email transmission fails."""
    pass


class EmailValidationError(Exception):
    """Custom exception raised when an email address is invalid."""
    pass


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.EMAILS_FROM_EMAIL
        self.sender_name = settings.EMAILS_FROM_NAME
        self.is_enabled = settings.EMAIL_ENABLED

    @staticmethod
    def validate_email_address(email: str) -> str:
        """Validates email format using Pydantic TypeAdapter."""
        clean = email.strip()
        try:
            TypeAdapter(EmailStr).validate_python(clean)
            return clean
        except Exception:
            raise EmailValidationError(f"Invalid recipient email format: '{clean}'")

    @staticmethod
    def mask_email(email: str) -> str:
        """Masks email address for privacy-compliant logging, e.g. j***n@domain.com."""
        parts = email.split("@")
        if len(parts) == 2 and len(parts[0]) > 2:
            return f"{parts[0][0]}***{parts[0][-1]}@{parts[1]}"
        return "***@***"

    def format_report_plain_text(self, patient: Patient, report: Report) -> str:
        """Constructs plain text fallback of the 4-week glucose clinical report."""
        averages = report.weekly_averages or {}
        stages = report.weekly_stages or {}

        lines = [
            "=" * 60,
            "SPUNDAN HOSPITAL - PATIENT GLUCOSE MONITORING REPORT",
            "=" * 60,
            f"Patient ID:     {patient.patient_id}",
            f"Patient Name:   {patient.name}",
            f"Current Stage:  {report.current_stage}",
            f"4-Week Trend:   {report.trend.capitalize()}",
            "-" * 60,
            "4-WEEK GLUCOSE SUMMARY:",
        ]

        for w in range(1, 5):
            k = f"week_{w}"
            avg = averages.get(k)
            avg_str = f"{avg:.1f} mg/dL" if avg is not None else "No data"
            stage = stages.get(k, "Insufficient Data")
            lines.append(f"  Week {w}: {avg_str:<12} | Stage: {stage}")

        lines.extend([
            "-" * 60,
            "CLINICAL AI SUMMARY:",
            report.ai_summary,
            "=" * 60,
            "Notice: This is an automated clinical notification from the Hospital Glucose Care System.",
        ])

        return "\n".join(lines)

    def format_report_html(self, patient: Patient, report: Report) -> str:
        """Constructs responsive, high-contrast HTML email report."""
        averages = report.weekly_averages or {}
        stages = report.weekly_stages or {}

        rows_html = ""
        for week_num in range(1, 5):
            w_key = f"week_{week_num}"
            avg = averages.get(w_key)
            avg_str = f"{avg:.1f} mg/dL" if avg is not None else "No Data"
            stage = stages.get(w_key, "Insufficient Data")

            badge_color = "#10b981"  # normal
            if stage == "Pre-diabetes":
                badge_color = "#f59e0b"
            elif stage == "Diabetes":
                badge_color = "#ef4444"
            elif stage == "Hypoglycemia":
                badge_color = "#8b5cf6"

            rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px 16px; font-weight: 600; color: #1e293b;">Week {week_num}</td>
                <td style="padding: 12px 16px; color: #334155; font-family: monospace; font-weight: 600;">{avg_str}</td>
                <td style="padding: 12px 16px;">
                    <span style="background-color: {badge_color}20; color: {badge_color}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;">
                        {stage}
                    </span>
                </td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Patient Glucose Report</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #334155;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="background: linear-gradient(135deg, #0ea5e9, #0284c7); padding: 24px; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 20px; font-weight: 700;">Spundan Hospital Glucose Monitoring</h1>
                    <p style="margin: 4px 0 0; font-size: 14px; opacity: 0.9;">Continuous Glycemic Clinical Report</p>
                </div>
                
                <div style="padding: 24px;">
                    <div style="background-color: #f1f5f9; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr>
                                <td style="padding: 4px 0; color: #64748b; width: 140px;">Patient Name:</td>
                                <td style="padding: 4px 0; font-weight: 600; color: #0f172a;">{patient.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Patient ID:</td>
                                <td style="padding: 4px 0; font-weight: 600; color: #0f172a;">{patient.patient_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">4-Week Trend:</td>
                                <td style="padding: 4px 0; font-weight: 600; text-transform: capitalize; color: #0f172a;">{report.trend}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Current Stage:</td>
                                <td style="padding: 4px 0; font-weight: 700; color: #0ea5e9;">{report.current_stage}</td>
                            </tr>
                        </table>
                    </div>

                    <h3 style="font-size: 16px; font-weight: 600; color: #0f172a; margin: 0 0 12px;">4-Week Glucose Breakdown</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 24px;">
                        <thead>
                            <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
                                <th style="padding: 10px 16px; color: #475569;">Period</th>
                                <th style="padding: 10px 16px; color: #475569;">Mean Glucose</th>
                                <th style="padding: 10px 16px; color: #475569;">Clinical Stage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>

                    <h3 style="font-size: 16px; font-weight: 600; color: #0f172a; margin: 0 0 8px;">AI Clinical Summary</h3>
                    <div style="background-color: #f8fafc; border-left: 4px solid #0ea5e9; padding: 14px 16px; font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 24px; border-radius: 0 6px 6px 0;">
                        {report.ai_summary}
                    </div>

                    <div style="border-top: 1px solid #e2e8f0; padding-top: 16px;">
                        <p style="font-size: 12px; color: #94a3b8; margin: 0; line-height: 1.5;">
                            This automated clinical notification was sent by the Spundan Hospital Patient Glucose Monitoring System.
                            Always consult your physician before making dietary or pharmacological changes.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    async def send_patient_report_email(
        self, patient: Patient, report: Report, timeout_sec: int = 10
    ) -> Dict[str, Any]:
        """Dispatches the report email to the patient with both HTML and plain-text alternatives."""
        # 1. Validate email address
        recipient = self.validate_email_address(patient.email)
        masked_recip = self.mask_email(recipient)
        subject = f"Clinical Glucose Monitoring Report - Patient {patient.patient_id}"

        logger.info("Initiating report email dispatch to patient %s (%s)", patient.patient_id, masked_recip)

        # 2. Check if running in mock/simulation mode
        if not self.is_enabled or not self.smtp_password or self.smtp_password == "app-password-placeholder":
            logger.info("Simulation mode active (EMAIL_ENABLED=False). Simulated email sent to %s", masked_recip)
            return {
                "status": "simulated",
                "recipient": recipient,
                "subject": subject,
                "message": f"4-week glucose report successfully dispatched to {recipient} (Simulated Delivery).",
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
            }

        # 3. SMTP transmission
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = recipient

            text_content = self.format_report_plain_text(patient, report)
            html_content = self.format_report_html(patient, report)

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=timeout_sec) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, [recipient], msg.as_string())

            logger.info("Email delivered via SMTP to %s", masked_recip)
            return {
                "status": "sent",
                "recipient": recipient,
                "subject": subject,
                "message": f"4-week glucose report sent to {recipient}.",
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
            }
        except (socket.timeout, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            logger.error("SMTP timeout/connection failure to %s", masked_recip)
            raise EmailDeliveryError(f"Email service connection timeout: {str(e)}")
        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failed for sender %s", self.sender_email)
            raise EmailDeliveryError("Email authentication failure. Please check provider credentials.")
        except Exception as e:
            logger.error("SMTP error dispatching email to %s: %s", masked_recip, str(e))
            raise EmailDeliveryError(f"Failed to transmit email to {masked_recip}: {str(e)}")
