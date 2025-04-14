from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password', 'confirm_password', 'role']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'address',
            'profile_image',
            'bio',
            'headline',
            'expertise',
            'website',
            'social_links'
        ]
        read_only_fields = ['email', 'username', 'role']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add full image URL if profile image exists
        if data.get('profile_image'):
            request = self.context.get('request')
            if request:
                data['profile_image'] = request.build_absolute_uri(instance.profile_image.url)
        
        # Add full name
        data['full_name'] = f"{instance.first_name} {instance.last_name}".strip() or instance.username
        return data

    def validate_social_links(self, value):
        if value and not isinstance(value, dict):
            try:
                # Try to convert string to dict if it's a JSON string
                import json
                return json.loads(value)
            except:
                raise serializers.ValidationError("Social links must be a valid JSON object")
        return value or {}

    def update(self, instance, validated_data):
        try:
            # Update simple fields
            for field in ['first_name', 'last_name', 'phone_number', 'address', 
                         'bio', 'headline', 'expertise', 'website']:
                if field in validated_data:
                    setattr(instance, field, validated_data[field])

            # Handle profile image
            if 'profile_image' in validated_data:
                instance.profile_image = validated_data['profile_image']

            # Handle social links
            if 'social_links' in validated_data:
                instance.social_links = validated_data['social_links']

            instance.save()
            return instance
        except Exception as e:
            print(f"Error in update method: {str(e)}")
            raise

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'address',
            'profile_image',
            'bio',
            'headline',
            'expertise',
            'website',
            'social_links'
        ]  # Removed email and username from updateable fields

    def validate_social_links(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Social links must be a dictionary")
        
        allowed_platforms = {
            'linkedin': 'https://linkedin.com/',
            'github': 'https://github.com/',
            'twitter': 'https://twitter.com/',
            'youtube': 'https://youtube.com/',
            'facebook': 'https://facebook.com/',
            'instagram': 'https://instagram.com/',
            'website': ''
        }

        for platform, url in value.items():
            if platform not in allowed_platforms:
                raise serializers.ValidationError(f"Invalid platform: {platform}")
            
            if platform != 'website' and url and not url.startswith(allowed_platforms[platform]):
                raise serializers.ValidationError(
                    f"Invalid {platform} URL. Must start with {allowed_platforms[platform]}"
                )

        return value 