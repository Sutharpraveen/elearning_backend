from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'status': 'error',
            'message': '',
            'data': None,
            'errors': None,
        }

        if response.status_code == 400:
            custom_data['message'] = 'Validation Error'
            custom_data['errors'] = response.data
        elif response.status_code == 401:
            custom_data['message'] = 'Authentication failed. Please login again.'
        else:
            detail = response.data.get('detail') if isinstance(response.data, dict) else None
            custom_data['message'] = detail or str(exc)

        response.data = custom_data

    return response
