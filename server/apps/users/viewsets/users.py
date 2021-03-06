from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from django.contrib.auth.models import User

from apps.users.serializers.users import UserSerializer


class UserViewSet(CreateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        user = User(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
        )
        user.set_password(serializer.validated_data['password'])
        user.save()
        token = Token.objects.create(user=user).key
        response_data = {
            'id': user.id,
            'username': user.username,
            'token': token
        }

        return Response(response_data, status=HTTP_201_CREATED)
