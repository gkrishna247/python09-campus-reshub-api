from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", status_code=200):
    return Response({
        "status": "success",
        "data": data,
        "message": message
    }, status=status_code)

def error_response(errors=None, message="An error occurred", status_code=400):
    return Response({
        "status": "error",
        "errors": errors or [],
        "message": message
    }, status=status_code)

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize error format
        errors = []
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if isinstance(value, list):
                    for v in value:
                        errors.append({"field": key, "message": str(v)})
                else:
                    errors.append({"field": key, "message": str(value)})
        elif isinstance(response.data, list):
             for v in response.data:
                 errors.append({"message": str(v)})
        else:
             errors.append({"message": str(response.data)})

        response.data = {
            "status": "error",
            "errors": errors,
            "message": "An error occurred"
        }
    
    else:
        # Handle unhandled exceptions (500)
        # In production, we might want to log the exception here
        return Response({
            "status": "error",
            "errors": [{"message": str(exc)}],
            "message": "Internal Server Error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
