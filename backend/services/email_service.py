"""Email service for sending nudge invitations and notifications."""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to users."""
    
    def __init__(self):
        """Initialize email service."""
        # In production, this would initialize SMTP connection
        # For now, we'll log emails to console
        self.smtp_configured = False
        logger.info("Email service initialized (console mode)")
    
    async def send_nudge_email(
        self,
        to_email: str,
        from_user_name: str,
        trip_destination: str,
        trip_start_date: str,
        message: Optional[str] = None
    ) -> bool:
        """
        Send a nudge invitation email to a non-user.
        
        Args:
            to_email: Recipient email address
            from_user_name: Name of the user sending the nudge
            trip_destination: Trip destination
            trip_start_date: Trip start date
            message: Optional custom message
        
        Returns:
            True if email was sent successfully
        """
        try:
            # Format the email content
            subject = f"🦙 {from_user_name} invited you to pack for {trip_destination}!"
            
            body = f"""
Hi there!

{from_user_name} has invited you to help pack for an upcoming trip to {trip_destination} 
starting on {trip_start_date}.

{f'Personal message: {message}' if message else ''}

Alpaca is a family packing app that helps everyone stay organized and ensures
nothing gets left behind. Join us to:

• See what items you need to pack
• Check off items as you pack them
• Get reminders from family members
• Make packing fun for the whole family!

Click here to sign up and start packing: [SIGNUP_LINK]

Happy packing! 🎒
The Alpaca Team
            """
            
            # In production, send via SMTP
            # For now, log to console
            logger.info("=" * 60)
            logger.info("NUDGE EMAIL")
            logger.info("=" * 60)
            logger.info(f"To: {to_email}")
            logger.info(f"From: noreply@alpacaforyou.com")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info(body)
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send nudge email to {to_email}: {str(e)}")
            return False
    
    async def send_nudge_notification(
        self,
        to_email: str,
        from_user_name: str,
        trip_destination: str,
        trip_start_date: str,
        message: Optional[str] = None
    ) -> bool:
        """
        Send a nudge notification email to an existing user.
        
        Args:
            to_email: Recipient email address
            from_user_name: Name of the user sending the nudge
            trip_destination: Trip destination
            trip_start_date: Trip start date
            message: Optional custom message
        
        Returns:
            True if email was sent successfully
        """
        try:
            subject = f"🦙 {from_user_name} sent you a packing reminder!"
            
            body = f"""
Hi!

{from_user_name} sent you a reminder about packing for your trip to {trip_destination} 
on {trip_start_date}.

{f'Message: {message}' if message else ''}

Log in to Alpaca to check your packing list and mark items as packed.

[LOGIN_LINK]

Happy packing! 🎒
The Alpaca Team
            """
            
            # Log to console
            logger.info("=" * 60)
            logger.info("NUDGE NOTIFICATION")
            logger.info("=" * 60)
            logger.info(f"To: {to_email}")
            logger.info(f"From: noreply@alpacaforyou.com")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info(body)
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to {to_email}: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()