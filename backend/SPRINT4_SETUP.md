# Sprint 4: Collaboration Features Setup Guide

## Overview

Sprint 4 implements social collaboration features including:
- **Nudge System**: Send reminders to family members to pack their items
- **Trip Sharing**: Generate public share links for trips

## Features Implemented

### 1. Nudge System

The nudge system allows trip owners to send packing reminders to family members.

#### Key Features:
- **Smart Notifications**: Differentiates between users with accounts (in-app notifications) and non-users (email invitations)
- **Email Integration**: Sends invitation emails to non-users with trip context
- **Read Status Tracking**: Recipients can mark nudges as read
- **Trip Context**: Includes trip destination and dates in notifications

#### Endpoints:

**Send a Nudge**
```http
POST /api/v1/trips/{trip_id}/nudges
Authorization: Bearer <token>
Content-Type: application/json

{
  "person_id": "traveler_id",
  "message": "Don't forget to pack your favorite toys!"
}
```

**Get Nudges for Current User**
```http
GET /api/v1/nudges?unread_only=false
Authorization: Bearer <token>
```

**Mark Nudge as Read**
```http
PUT /api/v1/nudges/{nudge_id}/mark-read
Authorization: Bearer <token>
```

#### Models:

**NudgeRequest**
```python
{
  "person_id": str,        # ID of the traveler to nudge
  "message": str | None    # Optional custom message
}
```

**NudgeResponse**
```python
{
  "id": str,
  "trip_id": str,
  "from_user_id": str,
  "to_user_email": str,
  "message": str | None,
  "is_read": bool,
  "created_at": datetime,
  "trip_destination": str,
  "trip_start_date": str,
  "from_user_name": str | None
}
```

### 2. Trip Sharing

The trip sharing system allows trip owners to generate public share links.

#### Key Features:
- **Secure Tokens**: Uses cryptographically secure random tokens
- **Optional Expiration**: Share links can have expiration dates
- **Public Access**: No authentication required to view shared trips
- **Owner Control**: Only trip owners can generate/revoke share links

#### Endpoints:

**Generate Share Link**
```http
POST /api/v1/trips/{trip_id}/share
Authorization: Bearer <token>
Content-Type: application/json

{
  "expiration_days": 7  # Optional, null = no expiration
}
```

**Access Shared Trip (No Auth Required)**
```http
GET /api/v1/trips/shared/{share_token}
```

**Revoke Share Link**
```http
DELETE /api/v1/trips/{trip_id}/share
Authorization: Bearer <token>
```

#### Models:

**ShareRequest**
```python
{
  "expiration_days": int | None  # Optional expiration in days
}
```

**ShareResponse**
```python
{
  "share_url": str,              # Full URL to share
  "share_token": str,            # Token for API access
  "expires_at": datetime | None  # Expiration timestamp
}
```

### 3. Email Service

A simple email service for sending nudge notifications and invitations.

#### Current Implementation:
- **Console Logging**: Emails are logged to console for development
- **Production Ready**: Structured for easy SMTP integration

#### Email Types:

**Nudge Notification** (for existing users)
- Subject: "🦙 {sender} sent you a packing reminder!"
- Includes trip details and custom message
- Call-to-action to log in

**Nudge Invitation** (for non-users)
- Subject: "🦙 {sender} invited you to pack for {destination}!"
- Includes trip details and app benefits
- Call-to-action to sign up

## Database Schema Updates

### Trips Collection

Added fields to support sharing:
```python
{
  # ... existing fields ...
  "share_token": str | None,        # Secure share token
  "share_expires_at": datetime | None  # Optional expiration
}
```

### Nudges Collection (New)

```python
{
  "id": str,
  "trip_id": str,
  "from_user_id": str,
  "to_user_email": str,
  "message": str | None,
  "is_read": bool,
  "created_at": datetime
}
```

## Setup Instructions

### 1. Install Dependencies

No new dependencies required. All features use existing packages.

### 2. Environment Configuration

Update your `.env` file with optional email configuration:

```bash
# Email Service Configuration (Optional - for production)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_app_password
# SMTP_FROM_EMAIL=noreply@alpacaforyou.com
# SMTP_FROM_NAME=Alpaca For You
```

### 3. Database Indexes (Recommended)

Create indexes for optimal performance:

```javascript
// MongoDB shell commands
db.nudges.createIndex({ "to_user_email": 1, "created_at": -1 })
db.nudges.createIndex({ "trip_id": 1 })
db.trips.createIndex({ "share_token": 1 })
```

### 4. Start the Server

```bash
cd backend
uvicorn main:app --reload
```

## Testing

### Run Tests

```bash
# Run all collaboration tests
pytest backend/test_collaboration.py -v

# Run specific test class
pytest backend/test_collaboration.py::TestNudges -v
pytest backend/test_collaboration.py::TestTripSharing -v

# Run with coverage
pytest backend/test_collaboration.py --cov=backend/routes/collaboration --cov-report=html
```

### Test Coverage

The test suite includes:
- ✅ Sending nudges to existing users
- ✅ Sending nudges to non-users (email invites)
- ✅ Retrieving nudges with filtering
- ✅ Marking nudges as read
- ✅ Generating share links with/without expiration
- ✅ Accessing shared trips
- ✅ Handling expired share links
- ✅ Revoking share access
- ✅ Authorization checks
- ✅ Full workflow integration tests

## API Examples

### Example 1: Send a Nudge

```bash
curl -X POST http://localhost:8000/api/v1/trips/trip123/nudges \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "traveler456",
    "message": "Time to pack your swimsuit!"
  }'
```

### Example 2: Generate Share Link

```bash
curl -X POST http://localhost:8000/api/v1/trips/trip123/share \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expiration_days": 7
  }'
```

### Example 3: Access Shared Trip

```bash
curl http://localhost:8000/api/v1/trips/shared/abc123token
```

## Security Considerations

### Nudges
- ✅ Only trip owners can send nudges
- ✅ Users can only view their own nudges
- ✅ Email addresses are validated
- ✅ Rate limiting recommended for production

### Sharing
- ✅ Secure random tokens (32 bytes, URL-safe)
- ✅ Only trip owners can generate/revoke links
- ✅ Expiration validation on access
- ✅ Tokens are invalidated on revocation
- ⚠️ Consider adding view tracking in production
- ⚠️ Consider adding password protection option

## Production Considerations

### Email Service

To enable actual email sending in production:

1. **Choose an Email Provider**:
   - Gmail SMTP
   - SendGrid
   - AWS SES
   - Mailgun

2. **Update Email Service**:
   ```python
   # In backend/services/email_service.py
   # Replace console logging with actual SMTP
   import smtplib
   from email.mime.text import MIMEText
   from email.mime.multipart import MIMEMultipart
   ```

3. **Configure Environment Variables**:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

### Share Links

For production deployment:

1. **Update Share URL Generation**:
   ```python
   # In backend/routes/collaboration.py
   # Replace hardcoded domain with environment variable
   share_url = f"{settings.frontend_url}/shared/{share_token}"
   ```

2. **Add Rate Limiting**:
   ```python
   from slowapi import Limiter
   
   @limiter.limit("10/minute")
   async def generate_share_link(...):
       ...
   ```

3. **Add Analytics** (Optional):
   - Track share link views
   - Monitor popular trips
   - Analyze sharing patterns

## Troubleshooting

### Issue: Nudges not appearing

**Solution**: Check that:
1. Email addresses match between travelers and users
2. User is authenticated with correct email
3. Nudge was sent to the correct trip

### Issue: Share link expired immediately

**Solution**: Verify:
1. Server time is correct (UTC)
2. `expiration_days` is positive
3. Database stores datetime correctly

### Issue: Email not sending

**Solution**: 
1. Check console logs for email content
2. Verify SMTP configuration (if enabled)
3. Check email service logs

## Future Enhancements

Potential improvements for future sprints:

1. **Real-time Notifications**:
   - WebSocket support for instant nudges
   - Push notifications for mobile apps

2. **Enhanced Sharing**:
   - Password-protected share links
   - View-only vs. collaborative access
   - Share link analytics

3. **Nudge Features**:
   - Scheduled nudges
   - Recurring reminders
   - Nudge templates

4. **Email Improvements**:
   - HTML email templates
   - Email preferences
   - Unsubscribe functionality

## Related Documentation

- [Sprint 1: Authentication Setup](./AUTH_SETUP.md)
- [Sprint 2: Trip Management](./SPRINT2_SETUP.md)
- [Sprint 3: Packing Lists](./SPRINT3_SETUP.md)
- [API Documentation](http://localhost:8000/docs)

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review API documentation at `/docs`
3. Check server logs for detailed error messages

---

**Sprint 4 Status**: ✅ Complete

All collaboration features have been implemented and tested successfully!