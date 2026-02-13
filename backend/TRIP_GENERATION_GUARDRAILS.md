# Trip Generation Operational Guardrails

This document describes the operational guardrails and timeout policies implemented for robust trip generation with proper error handling and recovery.

## Overview

The async job system now includes comprehensive safeguards to prevent stuck jobs, handle timeouts gracefully, and provide fallback mechanisms through retry logic and automatic cleanup.

## Configuration

All timeout and retry settings are configurable in [`backend/config.py`](backend/config.py):

```python
# Trip Generation Timeout Configuration
trip_generation_timeout_seconds: int = 180  # 3 minutes max
trip_generation_warning_threshold_seconds: int = 60  # warn after 1 minute
job_cleanup_interval_seconds: int = 300  # cleanup every 5 minutes
job_max_age_hours: int = 1  # cleanup jobs older than 1 hour
job_max_retries: int = 2  # maximum retry attempts for transient failures
```

## Features Implemented

### 1. Timeout Enforcement

- **Hard Timeout**: Jobs are automatically terminated after 180 seconds (3 minutes)
- **Warning Threshold**: Logs a warning if a job takes longer than 60 seconds
- **Graceful Handling**: Timeout errors are caught and jobs are marked as failed with appropriate error messages

Implementation in [`backend/routes/trip_generation.py`](backend/routes/trip_generation.py):
- `process_trip_generation_job_with_timeout()` wraps job processing with `asyncio.wait_for()`
- Timeout errors trigger retry logic if applicable

### 2. Retry Logic

**Retry Policy**:
- Maximum 2 retry attempts for transient failures
- Exponential backoff: 2^retry_count seconds (2s, 4s)
- No retries for validation errors or permanent failures

**Error Classification**:
- `transient`: Network issues, timeouts, temporary API failures → **Retry**
- `validation`: Invalid input, missing required fields → **No Retry**
- `api_error`: API rate limits, quota exceeded → **No Retry**
- `timeout`: Job exceeded time limit → **Retry**
- `unknown`: Unclassified errors → **No Retry**

Implementation in [`backend/services/trip_generation_job_service.py`](backend/services/trip_generation_job_service.py):
- `should_retry()`: Determines if a job should be retried
- `increment_retry()`: Increments retry count and resets job to pending

### 3. Job Metadata Tracking

Enhanced [`TripGenerationJob`](backend/models/trip_generation_job.py) model includes:

```python
retry_count: int = 0              # Current retry attempt
max_retries: int = 2              # Maximum allowed retries
started_at: Optional[datetime]    # When job processing started
completed_at: Optional[datetime]  # When job finished (success or failure)
error_type: Optional[str]         # Classification of error
```

### 4. Automatic Cleanup

**Background Task**: Runs every 5 minutes to clean up old jobs
- Deletes completed/failed jobs older than 1 hour
- Prevents database bloat from accumulating job records
- Logs cleanup activity for monitoring

Implementation:
- `cleanup_old_jobs_task()` in [`backend/routes/trip_generation.py`](backend/routes/trip_generation.py)
- Started automatically on application startup in [`backend/main.py`](backend/main.py)

### 5. Monitoring Endpoints

#### Job Statistics
```
GET /api/v1/trip-generation/jobs/stats
```

Returns job counts by status:
```json
{
  "pending": 2,
  "processing": 1,
  "completed": 45,
  "failed": 3,
  "stuck": 0,
  "total": 51
}
```

#### Health Check
```
GET /api/v1/trip-generation/jobs/health
```

Reports system health based on stuck jobs and processing load:
```json
{
  "status": "healthy",
  "stuck_jobs_count": 0,
  "processing_jobs_count": 1,
  "timestamp": "2026-02-13T03:25:00.000Z"
}
```

Status values:
- `healthy`: No stuck jobs, processing count < 10
- `degraded`: Stuck jobs detected or high processing load

### 6. Structured Logging

All job operations include structured logging with context:

```python
logger.info(
    f"Job {job_id} completed successfully",
    extra={
        "job_id": job_id,
        "trip_id": trip.id,
        "user_id": job.user_id
    }
)
```

Log levels:
- `INFO`: Job lifecycle events (started, completed, retried)
- `WARNING`: Slow jobs, validation errors
- `ERROR`: Failures, timeouts, unexpected errors

## Error Handling Flow

```
Job Submitted
    ↓
Processing Started (with timeout wrapper)
    ↓
[Timeout Check] → Timeout? → Classify Error → Retry? → Increment & Retry
    ↓                                              ↓
[Error Check] → Error? → Classify Error → Retry? → Mark Failed
    ↓                                         ↓
Success → Mark Completed              Mark Failed
```

## Usage Examples

### Creating a Job
```python
POST /api/v1/trip-generation/jobs
{
  "destination": "Paris",
  "start_date": "2026-06-01",
  "end_date": "2026-06-07",
  "travelers": [...],
  "activities": ["sightseeing"],
  "transport": "plane"
}
```

Response includes retry information:
```json
{
  "jobId": "abc123",
  "status": "pending",
  "retryCount": 0,
  "createdAt": "2026-02-13T03:25:00.000Z",
  "updatedAt": "2026-02-13T03:25:00.000Z"
}
```

### Checking Job Status
```python
GET /api/v1/trip-generation/jobs/{job_id}
```

Response shows error details if failed:
```json
{
  "jobId": "abc123",
  "status": "failed",
  "error": "Job timed out after 180 seconds",
  "errorType": "timeout",
  "retryCount": 2,
  "createdAt": "2026-02-13T03:25:00.000Z",
  "updatedAt": "2026-02-13T03:31:00.000Z"
}
```

## Monitoring and Debugging

### Check System Health
```bash
curl http://localhost:8000/api/v1/trip-generation/jobs/health
```

### View Job Statistics
```bash
curl http://localhost:8000/api/v1/trip-generation/jobs/stats
```

### Log Analysis
Look for these log patterns:
- `Job {job_id} is taking longer than 60s` - Slow job warning
- `Job {job_id} timed out after 180s` - Timeout occurred
- `Retrying job {job_id} after {n}s backoff` - Retry initiated
- `Cleanup task deleted {n} old jobs` - Automatic cleanup ran

## Benefits

1. **Reliability**: Automatic retries for transient failures
2. **Visibility**: Comprehensive logging and monitoring endpoints
3. **Resource Management**: Automatic cleanup prevents database bloat
4. **User Experience**: Clear error messages and status tracking
5. **Operational Safety**: Timeouts prevent runaway jobs
6. **Debugging**: Structured logs with context for troubleshooting

## Future Enhancements

Potential improvements:
- Dead letter queue for permanently failed jobs
- Metrics export to monitoring systems (Prometheus, DataDog)
- Configurable retry strategies per error type
- Job priority queuing
- Rate limiting per user
- Partial result saving on timeout