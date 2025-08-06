from myapp.models import Report
from .models import *
from rest_framework import serializers # type: ignore

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        
        
class ProblemReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UssdReport
        fields = ['id', 'phone_number', 'open_space', 'description', 'reference_number', 'status']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'is_staff']


class ProfileImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['profile_image']

class ForwardedBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForwardedBooking
        fields = ['booking', 'ward_executive_description', 'forwarded_by']

# serializers.py
class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'profile_image']

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            return request.build_absolute_uri(obj.profile_image.url)
        return None




class OpenSpaceBookingSerializer(serializers.ModelSerializer):
    space_name = serializers.SerializerMethodField()

    class Meta:
        model = OpenSpaceBooking
        fields = '__all__'
        read_only_fields = ['user']
        extra_kwargs = {
            'space': {'required': False}
        }

    def get_space_name(self, obj):
        return obj.space.name if obj.space else None

    def create(self, validated_data):
        request = self.context.get('request')
        space_id = request.data.get('space_id') if request else None

        if not space_id:
            raise serializers.ValidationError({"space": "This field is required."})

        try:
            space = OpenSpace.objects.get(id=space_id)
        except OpenSpace.DoesNotExist:
            raise serializers.ValidationError({"space": "Open space not found."})

        if space.status == 'unavailable':
            raise serializers.ValidationError({"space": "This open space has already been booked and is unavailable."})

        validated_data.pop('space', None)
        validated_data['user'] = request.user
        booking = OpenSpaceBooking.objects.create(space=space, **validated_data)
        return booking



class OpenSpaceBookingListSerializer(serializers.ModelSerializer):
    space = serializers.StringRelatedField()

    class Meta:
        model = OpenSpaceBooking
        fields = ['space', 'username', 'contact', 'duration', 'purpose', 'district']
        read_only_fields = ['id', 'created_at']

