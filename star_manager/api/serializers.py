from django.contrib.auth.models import Group, User
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="api:user-detail")

    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class AllChatsSerializer(serializers.Serializer):
    chat_id = serializers.IntegerField()


class AccessLvlSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    chat_id = serializers.IntegerField()
    access_level = serializers.IntegerField()
