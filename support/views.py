from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

from .ai_assistant import get_support_assistant


@login_required
def support_page_view(request):
    """Render the support chat page."""
    context = {
        'user': request.user,
    }
    return render(request, 'support/support_page.html', context)


@login_required
@require_POST
def support_chat_api(request):
    """
    API endpoint for chat messages.
    Receives user message and returns AI assistant response.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'error': 'Message is required',
                'success': False
            }, status=400)
        
        # Get response from assistant
        assistant = get_support_assistant()
        result = assistant.get_response(user_message)
        
        return JsonResponse({
            'success': True,
            'response': result['response'],
            'category': result.get('category', 'general'),
            'suggestions': result.get('suggestions', []),
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'success': False
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)
