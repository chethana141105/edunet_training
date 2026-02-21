from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .ai_service import chat_with_ai

@login_required
@csrf_exempt
def chat_api(request):
    """API Endpoint for AJAX Chat Requests."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            
            if not message:
                return JsonResponse({'error': 'No message provided'}, status=400)
            
            response_text = chat_with_ai(request.user, message)
            
            return JsonResponse({'response': response_text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def chat_view(request):
    """Full-page chat interface (optional)."""
    return render(request, 'chatbot/chat.html')
