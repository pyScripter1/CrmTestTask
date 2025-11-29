from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import logging

from crm.serializers import UserSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint - returns auth token and user data

    POST /api/auth/login/
    {
        "username": "user",
        "password": "pass"
    }
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Please provide both username and password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        serializer = UserSerializer(user)

        return Response({
            "token": token.key,
            "user": serializer.data
        })

    except Exception as e:
        logger.error(f"Error in login_view: {str(e)}")
        return Response(
            {"error": "Login failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - deletes auth token

    POST /api/auth/logout/
    Headers: Authorization: Token <token>
    """
    try:
        request.user.auth_token.delete()
        return Response(
            {"message": "Successfully logged out"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error in logout_view: {str(e)}")
        return Response(
            {"error": "Logout failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Get current user info

    GET /api/auth/me/
    Headers: Authorization: Token <token>
    """
    try:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error in me_view: {str(e)}")
        return Response(
            {"error": "Failed to get user info", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
