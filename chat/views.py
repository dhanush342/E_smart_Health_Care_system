import json
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from chat.models import Message, UserProfile
from chat.serializers import MessageSerializer, UserSerializer


def index(request):
    if request.user.is_authenticated:
        return redirect('chats')
    if request.method == 'GET':
        return render(request, 'chat/index.html', {})
    if request.method == "POST":
        username, password = request.POST.get('username', ''), request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('chats')
        else:
            return HttpResponse('{"error": "User does not exist"}')


@csrf_exempt
def user_list(request, pk=None):
    """
    List all required users, or register a new user.
    Requires authentication to view user directories.
    """
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        if pk:
            users = User.objects.filter(id=pk)
        else:
            if request.user.groups.filter(name="PATIENT").exists():
                users = User.objects.filter(groups__name="DOCTOR")
            elif request.user.groups.filter(name="DOCTOR").exists():
                users = User.objects.filter(groups__name="PATIENT")
            else:
                users = User.objects.exclude(id=request.user.id)

            # Fallback to all other users if group filter returns none
            if not users.exists():
                users = User.objects.exclude(id=request.user.id)

        serializer = UserSerializer(users, many=True, context={'request': request})
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        # Only staff or registration endpoints should create users
        if not request.user.is_authenticated and not getattr(settings, 'ALLOW_ANONYMOUS_CHAT_REGISTER', False):
            return JsonResponse({'error': 'Registration via API is restricted. Please use the registration portal.'}, status=403)
        try:
            if request.content_type and 'application/json' in request.content_type:
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = JSONParser().parse(request)
        except Exception:
            data = request.POST.dict()

        try:
            username = data.get('username', '').strip()
            password = data.get('password', '')
            if not username or not password:
                return JsonResponse({'error': 'Username and password required.'}, status=400)
            user = User.objects.create_user(username=username, password=password)
            UserProfile.objects.get_or_create(user=user)
            return JsonResponse({'username': user.username, 'id': user.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def message_list(request, sender=None, receiver=None):
    """
    List unread messages between sender and receiver, or create a new message.
    Protected: Only participants in the conversation or staff can access messages.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    if request.method == 'GET':
        if sender and receiver:
            # Enforce authorization: User must be sender or receiver
            if request.user.id not in (int(sender), int(receiver)) and not request.user.is_staff:
                return JsonResponse({'error': 'Forbidden: You cannot access other users messages.'}, status=403)

            messages = Message.objects.filter(sender_id=sender, receiver_id=receiver, is_read=False).order_by('timestamp')
            serializer = MessageSerializer(messages, many=True, context={'request': request})
            for message in messages:
                message.is_read = True
                message.save()
            return JsonResponse(serializer.data, safe=False)
        return JsonResponse([], safe=False)

    elif request.method == 'POST':
        try:
            if request.content_type and 'application/json' in request.content_type:
                data = json.loads(request.body.decode('utf-8'))
            elif request.body:
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except Exception:
                    data = JSONParser().parse(request)
            else:
                data = request.POST.dict()
        except Exception:
            data = JSONParser().parse(request)

        # Enforce that the sender is the currently authenticated user to prevent message spoofing
        if isinstance(data, dict):
            # Sanitize message body to prevent stored XSS
            if 'message' in data and isinstance(data['message'], str):
                import html
                data['message'] = html.escape(data['message'])

            # Bind sender to request.user
            data['sender'] = request.user.username

            if 'receiver' in data and str(data['receiver']).isdigit():
                try:
                    data['receiver'] = User.objects.get(id=int(data['receiver'])).username
                except User.DoesNotExist:
                    pass

        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


def register_view(request):
    """
    Render registration template
    """
    if request.user.is_authenticated:
        return redirect('chats')
    return render(request, 'chat/register.html', {})


def chat_view(request):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == "GET":
        return render(request, 'chat/chat.html',
                      {'users': User.objects.exclude(username=request.user.username)})


def message_view(request, sender, receiver):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == "GET":
        receiver_user = get_object_or_404(User, id=receiver)
        # Mark unread messages sent by this receiver to the current user as read
        Message.objects.filter(sender_id=receiver, receiver_id=request.user.id, is_read=False).update(is_read=True)
        messages = Message.objects.filter(
            Q(sender_id=sender, receiver_id=receiver) | Q(sender_id=receiver, receiver_id=sender)
        ).order_by('timestamp')
        return render(request, "chat/messages.html", {
            'users': User.objects.exclude(username=request.user.username),
            'receiver': receiver_user,
            'messages': messages
        })

