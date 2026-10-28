from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ConflictError(Exception):
    """Raised by service-layer code when an operation conflicts with
    existing state (e.g. illegal state transition). Translated to HTTP 409."""

    def __init__(self, message="Conflict with current state", detail=None):
        self.message = message
        self.detail = detail or message
        super().__init__(message)


def custom_exception_handler(exc, context):
    """Extends DRF's default exception handler so service-layer errors
    (ConflictError) come back as clean, structured 409 responses instead of
    500s."""
    if isinstance(exc, ConflictError):
        return Response({"detail": exc.detail}, status=status.HTTP_409_CONFLICT)

    if isinstance(exc, IntegrityError):
        return Response(
            {"detail": "This operation conflicts with existing data."},
            status=status.HTTP_409_CONFLICT,
        )

    response = exception_handler(exc, context)
    return response
