from rest_framework.response import Response
from rest_framework import status


def api_error(code: str, message: str, hint: str = "", http_status=status.HTTP_400_BAD_REQUEST):
    return Response({
        "error": {
            "code": code,
            "message": message,
            "hint": hint
        }
    }, status=http_status)



