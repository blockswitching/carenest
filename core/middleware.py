"""
Middleware for consistent API response envelope.
All API responses wrapped in: {"success": bool, "data": ..., "message": ""}
Error responses: {"success": false, "errors": {...}, "message": ""}
"""

import json

from django.utils.deprecation import MiddlewareMixin


class ResponseEnvelopeMiddleware(MiddlewareMixin):
    """
    Wraps all /api/ JSON responses in a consistent envelope format.
    Skips admin, schema, and non-JSON responses.
    """

    def process_response(self, request, response):
        # Only wrap API responses
        path = request.path
        if not path.startswith("/api/"):
            return response

        # Skip schema/docs endpoints
        if any(path.startswith(p) for p in ["/api/schema", "/api/docs", "/api/redoc"]):
            return response

        # Only wrap JSON responses
        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return response

        # Don't wrap if already wrapped (e.g., by exception handler)
        try:
            data = json.loads(response.content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return response

        # Skip if already in envelope format
        if isinstance(data, dict) and "success" in data:
            return response

        # Determine success
        is_success = 200 <= response.status_code < 400

        if is_success:
            envelope = {
                "success": True,
                "data": data,
                "message": "",
            }
        else:
            # Extract error message
            message = ""
            errors = {}

            if isinstance(data, dict):
                if "detail" in data:
                    message = data["detail"]
                    errors = {}
                else:
                    # Field-level validation errors
                    errors = data
                    message = "Validation failed."
            elif isinstance(data, list):
                message = data[0] if data else "An error occurred."
                errors = {"non_field_errors": data}
            else:
                message = str(data)

            envelope = {
                "success": False,
                "errors": errors,
                "message": message,
            }

        response.content = json.dumps(envelope, ensure_ascii=False)
        response["Content-Length"] = len(response.content)
        return response
