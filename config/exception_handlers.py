"""
Custom exception handler for Django REST Framework.

All error responses follow the format:
{
    "success": false,
    "message": "description",
    "errors": { ... }
}
"""

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Handle exceptions and return consistent JSON error responses."""

    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is not None:
        # ── Validation errors ────────────────────────────────────────────
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": response.data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Not found ────────────────────────────────────────────────────
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return Response(
                {
                    "success": False,
                    "message": "Resource not found.",
                    "errors": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Method not allowed ───────────────────────────────────────────
        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            return Response(
                {
                    "success": False,
                    "message": "Method not allowed.",
                    "errors": {},
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        # ── All other DRF-handled errors ─────────────────────────────────
        return Response(
            {
                "success": False,
                "message": str(response.data.get("detail", "An error occurred.")),
                "errors": response.data,
            },
            status=response.status_code,
        )

    # ── IntegrityError (duplicate email, double-booking, etc.) ───────────
    if isinstance(exc, IntegrityError):
        return Response(
            {
                "success": False,
                "message": "A database integrity error occurred. Possible duplicate entry.",
                "errors": {"detail": str(exc)},
            },
            status=status.HTTP_409_CONFLICT,
        )

    # ── Unhandled 500 errors ─────────────────────────────────────────────
    return Response(
        {
            "success": False,
            "message": "An internal server error occurred.",
            "errors": {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
