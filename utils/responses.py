from rest_framework.response import Response


def custom_response(
    *,
    data=None,
    message="",
    status_code=200,
    success=True
):
    return Response(
        {
            "success": success,
            "message": message,
            "data": data,
        },
        status=status_code
    )
