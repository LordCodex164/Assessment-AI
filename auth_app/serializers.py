# exams/serializers.py  (or create accounts/serializers.py if separate app)

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password", style={'input_type': 'password'})
    user_type = serializers.ChoiceField(
        choices=['student', 'staff'],
        default='student',
        required=False  # Optional, defaults to 'student'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'user_type']
        extra_kwargs = {'email': {'required': True}}  # email is required

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        print("Validated Data:", validated_data)
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            user_type= validated_data["user_type"]  # default user type as student
        )
    
        user.set_password(validated_data["password"])
        user.save()
        return user

    # Override to return JWT tokens immediately after registration
    def to_representation(self, instance):
        return {
            'user': {
                'username': instance.username,
                'email': instance.email,
                'user_type': instance.user_type,
            }
        }
    
class GetUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', "user_type")

    def get_user(self, obj):
        user = User.objects.get(id=obj.id)
        if user.is_anonymous:
            raise serializers.ValidationError({"you are not signed in"})
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            "user_type": user.user_type,
        }


    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
            "user_type": instance.user_type,
        }

class LoginUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("password", "email")
        read_only_fields = ['password']

    def validate_user(self, data):
        try:
            user = User.objects.get(email = data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"User with this email does not exist"})
        if not user:
            raise serializers.ValidationError({"Invalid email or password"})
        password = data.get("password")
        if not user.check_password(password):
            raise serializers.ValidationError({"Invalid email or password"})
        refresh = RefreshToken.for_user(user)
        return {
            "user": {
             'id': user.id,
            'username': user.username,
            'email': user.email,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }