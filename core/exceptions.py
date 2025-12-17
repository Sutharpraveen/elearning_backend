from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Add custom error message
        if isinstance(response.data, dict):
            response.data = {
                'status': 'error',
                'message': response.data.get('detail', str(exc)),
                'data': None
            }
        else:
            response.data = {
                'status': 'error',
                'message': str(exc),
                'data': None
            }

    return response 