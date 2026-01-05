from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework import status
from  .serializers import RegisterSerializer, GetUserSerializer, LoginUserSerializer
from rest_framework.views import APIView
from utils.responses import custom_response
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        print(">>> Request Data:", request.data)
        
        serializer = RegisterSerializer(data=request.data)
        
        # ✅ FIX: Proper error handling
        if not serializer.is_valid():
            print(">>> Validation Errors:", serializer.errors)
            return custom_response(
                data=serializer.errors,
                message="Validation failed",
                success=False,
                status_code=400
            )
        
        try:
            # Save user
            user = serializer.save()
            print(">>> User Created Successfully:", user.id)
            
            # Get the response data (includes tokens)
            response_data = serializer.to_representation(user)
            
            return custom_response(
                data=response_data,
                message="User registered successfully",
                status_code=201
            )
            
        except Exception as e:
            print(">>> Registration Error:", str(e))
            return custom_response(
                message=f"Registration failed: {str(e)}",
                success=False,
                status_code=500
            )
class LoginUserView(APIView):
    def post(self, request):
        serializer = LoginUserSerializer(data= request.data)
        if serializer.is_valid():
            valid_user = serializer.validate_user(request.data)
            return custom_response(data=valid_user, message="User Login Successful")
        raise APIException("something went wrong")

class GetUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user is NotAuthenticated:
            return NotAuthenticated("Please Login to perform this action")
        serializer = GetUserSerializer(request.user)
        user = serializer.get_user(request.user)
        return custom_response(data=serializer.data, status_code=status.HTTP_200_OK, message="User fetched successfully")
    