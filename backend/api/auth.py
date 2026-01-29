"""
Multi-tenant authentication endpoints
Login, School selection, Token management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q

from backend.users.models import User
from backend.core.models import School
from backend.api.serializers import UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def school_login(request):
    """
    Tenant-aware login endpoint
    
    Request:
    {
        "school_code": "MUNTECH001",
        "username": "teacher1",
        "password": "password"
    }
    
    Response:
    {
        "access": "...",
        "refresh": "...",
        "school": {...},
        "user": {...}
    }
    """
    school_code = request.data.get('school_code')
    username = request.data.get('username')
    password = request.data.get('password')

    if not all([school_code, username, password]):
        return Response(
            {'error': 'school_code, username, and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        school = School.objects.get(code=school_code)
    except School.DoesNotExist:
        return Response(
            {'error': f'School "{school_code}" not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check if user belongs to this school
    if user.school and user.school != school:
        return Response(
            {'error': 'This user does not belong to the selected school'},
            status=status.HTTP_403_FORBIDDEN
        )

    # If user has no school assigned, assign it now
    if not user.school:
        user.school = school
        user.save()

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'school': {
            'id': school.id,
            'name': school.name,
            'code': school.code,
        },
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'school_id': user.school_id,
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_schools(request):
    """
    Get available schools for the authenticated user.
    Superusers see all schools, regular users see only their school.
    """
    if request.user.is_superuser:
        schools = School.objects.all()
    elif request.user.school:
        schools = School.objects.filter(id=request.user.school_id)
    else:
        schools = School.objects.none()

    data = [
        {
            'id': school.id,
            'name': school.name,
            'code': school.code,
            'country': school.country,
            'county': school.county,
        }
        for school in schools
    ]

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_school(request):
    """
    Switch active school for superuser/admin.
    
    Request:
    {
        "school_id": 1
    }
    """
    if not request.user.is_superuser and not request.user.is_staff:
        return Response(
            {'error': 'Only administrators can switch schools'},
            status=status.HTTP_403_FORBIDDEN
        )

    school_id = request.data.get('school_id')
    if not school_id:
        return Response(
            {'error': 'school_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        school = School.objects.get(id=school_id)
    except School.DoesNotExist:
        return Response(
            {'error': 'School not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Update user's school
    request.user.school = school
    request.user.save()

    return Response({
        'success': True,
        'school': {
            'id': school.id,
            'name': school.name,
            'code': school.code,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint.
    Client should delete tokens from localStorage.
    """
    return Response(
        {'message': 'Logged out successfully'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_school(request):
    """
    Get current user's school context
    """
    if not request.user.school:
        return Response(
            {'error': 'User not assigned to any school'},
            status=status.HTTP_400_BAD_REQUEST
        )

    school = request.user.school
    return Response({
        'id': school.id,
        'name': school.name,
        'code': school.code,
        'country': school.country,
        'county': school.county,
        'user_id': request.user.id,
        'username': request.user.username,
    }, status=status.HTTP_200_OK)
