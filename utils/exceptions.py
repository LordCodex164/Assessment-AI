from rest_framework.views import exception_handler

from utils import responses

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print("res", response)
    if response is None: 
       return responses.custom_response(
           status_code=500,
           message="Internal server error",
           data= None
       )

    if response.status_code: 
       return responses.custom_response(
           status_code= response.status_code,
           message= response.status_text,
           data= None,
           success= False
       )

    if response is not None:
        response.data = {
            "success": False,
            "message": response.data.get("detail", "An error occurred"),
            "data": None
        }
    

        # Case 1: Simple error with 'detail' (e.g., NotFound, PermissionDenied)
        if isinstance(response.data, dict) and "detail" in response.data:
            response.data["message"] = response.data["detail"]
            
            print("r", response.data)

        if isinstance(response.data, dict) and "success" in response.data:
            response.data["message"] = response.data["message"]

        # Case 3: List or string (rare)
        else:
            response.data["message"] = str(response.data or "An error occurred")

        response.data = response
    return response
