from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import AuthenticationFailed
from .models import RoleChangeRequest
from core.validators import CustomPasswordValidator

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'account_status', 'approval_status']
        read_only_fields = fields

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['STUDENT', 'FACULTY', 'STAFF'])

    class Meta:
        model = User
        fields = ['email', 'name', 'phone', 'password', 'confirm_password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_email(self, value):
        if User.all_objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        
        # Use custom password validator
        validator = CustomPasswordValidator()
        # validate() raises ValidationError if invalid
        validator.validate(data['password'])
        
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        role = validated_data.get('role')
        email = validated_data.get('email')
        
        # Determine approval status
        if email.endswith("@ksrct.net"):
            approval_status = "APPROVED"
        else:
            approval_status = "PENDING"
            
        user = User.objects.create_user(
            email=email,
            password=validated_data['password'],
            name=validated_data['name'],
            phone=validated_data.get('phone'),
            role=role,
            account_status="ACTIVE",
            approval_status=approval_status
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user_id'] = user.id
        token['email'] = user.email
        token['role'] = user.role
        token['account_status'] = user.account_status
        token['approval_status'] = user.approval_status

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        if self.user.account_status == "INACTIVE":
            raise AuthenticationFailed("Account is inactive. Contact administrator.")
            
        data['user'] = UserMinimalSerializer(self.user).data
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone', 'role', 
            'account_status', 'approval_status', 'rejection_reason', 
            'is_email_verified', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at', 'last_login']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'phone', 'role', 'account_status', 'approval_status', 'rejection_reason']
        # Email is NOT included

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone', 'role', 
            'account_status', 'approval_status', 'rejection_reason', 
            'is_email_verified', 'created_at'
        ]
        read_only_fields = [
            'id', 'email', 'role', 
            'account_status', 'approval_status', 'rejection_reason', 
            'is_email_verified', 'created_at'
        ]

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validator = CustomPasswordValidator()
        validator.validate(value)
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})
        return data

class RegistrationApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rejection reason is required."})
        return data

class RoleChangeRequestCreateSerializer(serializers.ModelSerializer):
    requested_role = serializers.ChoiceField(choices=['STUDENT', 'FACULTY', 'STAFF'])

    class Meta:
        model = RoleChangeRequest
        fields = ['requested_role']

    def validate_requested_role(self, value):
        user = self.context['request'].user
        if value == user.role:
            raise serializers.ValidationError("Requested role cannot be the same as current role.")
        return value

class RoleChangeRequestSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    reviewed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = RoleChangeRequest
        fields = [
            'id', 'user', 'current_role', 'requested_role', 
            'status', 'rejection_reason', 'reviewed_by', 
            'reviewed_at', 'created_at'
        ]
        read_only_fields = fields

class RoleChangeReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rejection reason is required."})
        return data
