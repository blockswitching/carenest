"""
Custom exception handler for consistent error responses.
"""

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns errors in envelope format.
    """
    response = exception_handler(exc, context)

    if response is not None:
        errors = {}
        message = ""

        if isinstance(response.data, dict):
            if "detail" in response.data:
                message = str(response.data["detail"])
            else:
                errors = response.data
                message = "Validation failed."
        elif isinstance(response.data, list):
            message = response.data[0] if response.data else "An error occurred."
            errors = {"non_field_errors": response.data}

        response.data = {
            "success": False,
            "errors": errors,
            "message": message,
        }

    return response


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable. Please try again later."
    default_code = "service_unavailable"
