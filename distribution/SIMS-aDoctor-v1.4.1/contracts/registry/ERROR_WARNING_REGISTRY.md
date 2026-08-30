# Error and Warning Registry v0.1.0

## Error categories
VALIDATION / AUTHENTICATION / AUTHORIZATION / VERSION_MISMATCH /
RESOURCE_NOT_FOUND / CONFLICT / TEMPORARY_FAILURE / RATE_LIMIT /
SYSTEM_FAILURE

## Warning severity
INFO / WARNING / HIGH

Errors use:
```json
{
  "success": false,
  "error": {
    "code": "ACTIVE_TREATMENT_CONFLICT",
    "category": "CONFLICT",
    "message": "対象記事では別の処置が進行中です。",
    "retryable": false,
    "details": {}
  }
}
```
