import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.core.logging import logger
from app.models.patient import Patient
from app.models.report import Report


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.EMAILS_FROM_EMAIL
        self.sender_name = settings.EMAILS_FROM_NAME
        self.is_enabled = settings.EMAIL_ENABLED

    def format_report_html(self, patient: Patient, report: Report) -> str:
        """Constructs an elegant, responsive HTML email report for the patient."""
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
                <td style="padding: 12px 16px; color: #334155; font-family: monospace;">{avg_str}</td>
                <td style="padding: 12px 16px;">
                    <span style="background-color: {badge_color}20; color: {badge_color}; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600;">
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
                    <h1 style="margin: 0; font-size: 20px; font-weight: 700;">Hospital Clinical Glucose Report</h1>
                    <p style="margin: 4px 0 0; font-size: 14px; opacity: 0.9;">Continuous Glycemic Monitoring Summary</p>
                </div>
                
                <div style="padding: 24px;">
                    <div style="background-color: #f1f5f9; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Patient Name:</td>
                                <td style="padding: 4px 0; font-weight: 600; color: #0f172a;">{patient.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Patient ID:</td>
                                <td style="padding: 4px 0; font-weight: 600; color: #0f172a;">{patient.patient_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Overall Trend:</td>
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
                                <th style="padding: 10px 16px; color: #475569;">Stage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>

                    <h3 style="font-size: 16px; font-weight: 600; color: #0f172a; margin: 0 0 8px;">Clinical Summary</h3>
                    <div style="background-color: #f8fafc; border-left: 4px solid #0ea5e9; padding: 12px 16px; font-size: 14px; line-height: 1.6; color: #334155; margin-bottom: 24px;">
                        {report.ai_summary}
                    </div>

                    <p style="font-size: 12px; color: #94a3b8; margin: 0; line-height: 1.5;">
                        This automated clinical summary is generated by the Spundan Hospital Patient Glucose Monitoring System.
                        Always consult your primary endocrinologist or physician regarding personal dietary or medication adjustments.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    async def send_patient_report_email(self, patient: Patient, report: Report) -> Dict[str, Any]:
        """Dispatches the report email to the patient. If SMTP credentials are not configured or
        EMAIL_ENABLED=False, safely simulates delivery in development/testing.
        """
        recipient = patient.email
        subject = f"Clinical Glucose Monitoring Report - Patient {patient.patient_id}"
        html_content = self.format_report_html(patient, report)

        logger.info(
            "Preparing glucose report email dispatch to patient %s (%s)",
            patient.patient_id,
            recipient,
        )

        if not self.is_enabled or not self.smtp_password:
            logger.info(
                "Email delivery simulated successfully for %s (EMAIL_ENABLED=False/mock mode)",
                recipient,
            )
            return {
                "status": "delivered_mock",
                "recipient": recipient,
                "subject": subject,
                "message": f"Report successfully delivered to {recipient} (Simulated).",
                "dispatched_at": datetime.now().isoformat(),
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = recipient

            part = MIMEText(html_content, "html")
            msg.attach(part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, [recipient], msg.as_string())

            logger.info("Email successfully sent via SMTP to %s", recipient)
            return {
                "status": "sent",
                "recipient": recipient,
                "subject": subject,
                "message": f"Report successfully sent to {recipient}.",
                "dispatched_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("SMTP delivery failure to %s: %s", recipient, str(e))
            raise RuntimeError(f"Email dispatch to {recipient} failed: {str(e)}")
