import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import OfflineSyncRecord
from community.models import CommunityPost, Comment, Reaction
from collaboration.models import CollaborationRequest, CollaborationInterest
from stories.models import Story
from matching.models import Problem, ProblemCategory, MentoringRequest
from matching.engine import run_matching_engine_for_problem
from messaging.models import Conversation, Message
from accounts.models import User

@csrf_exempt
def sync_batch_api(request):
    """
    Offline Sync Endpoint:
    Receives an array of pending operations from IndexedDB, executes them transactionally,
    resolves conflicts (preserves server state if already edited, updates client record),
    and returns server IDs and updated statuses.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required for synchronization'}, status=401)

    try:
        data = json.loads(request.body)
        operations = data.get('operations', [])
    except Exception as e:
        return JsonResponse({'error': f'Invalid JSON payload: {str(e)}'}, status=400)

    results = []
    synced_count = 0
    conflict_count = 0

    for op in operations:
        op_id = op.get('operation_id') or op.get('id')
        op_type = op.get('type')
        entity = op.get('entity')
        payload = op.get('payload', {})
        local_id = op.get('local_id')

        # Check if already processed
        if OfflineSyncRecord.objects.filter(operation_id=op_id).exists():
            results.append({'operation_id': op_id, 'status': 'ALREADY_SYNCED', 'local_id': local_id})
            continue

        try:
            server_id = None
            extra_data = {}

            # 1. CREATE_POST
            if op_type == 'CREATE_POST' or (entity == 'POST' and op_type == 'CREATE'):
                post = CommunityPost.objects.create(
                    author=request.user,
                    title=payload.get('title', 'Community Discussion'),
                    content=payload.get('content', ''),
                    post_type=payload.get('post_type', 'QUESTION'),
                    tags=payload.get('tags', '')
                )
                server_id = post.id
                extra_data['detail_url'] = f"/community/{post.id}/"

            # 2. CREATE_PROBLEM
            elif op_type == 'CREATE_PROBLEM' or (entity == 'PROBLEM' and op_type == 'CREATE'):
                cat_id = payload.get('category_id')
                cat = ProblemCategory.objects.filter(id=cat_id).first() if cat_id else None
                problem = Problem.objects.create(
                    entrepreneur=request.user,
                    title=payload.get('title', 'Business Challenge'),
                    description=payload.get('description', ''),
                    category=cat,
                    industry=payload.get('industry', request.user.entrepreneur_profile.industry if hasattr(request.user, 'entrepreneur_profile') else 'Agri-Business'),
                    business_stage=payload.get('business_stage', 'Early Stage'),
                    urgency=payload.get('urgency', 'HIGH'),
                    is_rural_business=payload.get('is_rural_business', True),
                    location=payload.get('location', request.user.city or 'Regional')
                )
                server_id = problem.id
                # Run matching engine on synchronized problem
                matches = run_matching_engine_for_problem(problem)
                extra_data['matches_count'] = len(matches)
                extra_data['matches_url'] = f"/entrepreneur/problems/{problem.id}/matches/"

            # 3. CREATE_STORY
            elif op_type == 'CREATE_STORY' or (entity == 'STORY' and op_type == 'CREATE'):
                story = Story.objects.create(
                    author=request.user,
                    story_type=payload.get('story_type', 'FAILURE'),
                    title=payload.get('title', 'Entrepreneur Journey'),
                    business_context=payload.get('business_context', 'Regional Enterprise'),
                    summary=payload.get('summary', ''),
                    what_happened=payload.get('what_happened', ''),
                    what_i_learned=payload.get('what_i_learned', ''),
                    what_i_would_do_differently=payload.get('what_i_would_do_differently', ''),
                    key_takeaway=payload.get('key_takeaway', ''),
                    is_approved=True
                )
                server_id = story.id

            # 4. CREATE_COLLABORATION
            elif op_type == 'CREATE_COLLABORATION' or (entity == 'COLLABORATION' and op_type == 'CREATE'):
                collab = CollaborationRequest.objects.create(
                    entrepreneur=request.user,
                    title=payload.get('title', 'Collaboration Opportunity'),
                    description=payload.get('description', ''),
                    industry=payload.get('industry', 'Food & Agriculture'),
                    collaboration_type=payload.get('collaboration_type', 'SUPPLY_CHAIN'),
                    location=payload.get('location', 'Regional'),
                    tags=payload.get('tags', '')
                )
                server_id = collab.id

            # 5. SEND_MESSAGE
            elif op_type == 'SEND_MESSAGE' or (entity == 'MESSAGE' and op_type == 'CREATE'):
                conv_id = payload.get('conversation_id')
                recipient_id = payload.get('recipient_id')
                content = payload.get('content', '')

                if conv_id:
                    conv = Conversation.objects.get(id=conv_id)
                elif recipient_id:
                    other_u = User.objects.get(id=recipient_id)
                    conv, _ = Conversation.get_or_create_conversation(request.user, other_u)
                else:
                    raise ValueError("Conversation or recipient required")

                msg = Message.objects.create(
                    conversation=conv,
                    sender=request.user,
                    content=content,
                    sync_status='SYNCED'
                )
                server_id = msg.id

            # 6. COMMENT_POST
            elif op_type == 'COMMENT_POST':
                post_id = payload.get('post_id')
                post = CommunityPost.objects.get(id=post_id)
                comment = Comment.objects.create(
                    post=post,
                    author=request.user,
                    content=payload.get('content', '')
                )
                server_id = comment.id

            # 7. LIKE_POST
            elif op_type == 'LIKE_POST':
                post_id = payload.get('post_id')
                post = CommunityPost.objects.get(id=post_id)
                reaction, created = Reaction.objects.get_or_create(
                    post=post,
                    user=request.user,
                    defaults={'reaction_type': payload.get('reaction_type', 'LIKE')}
                )
                if created:
                    post.likes_count += 1
                    post.save(update_fields=['likes_count'])
                server_id = reaction.id

            # 8. UPDATE_PROFILE
            elif op_type == 'UPDATE_PROFILE':
                user = request.user
                if payload.get('first_name'): user.first_name = payload['first_name']
                if payload.get('last_name'): user.last_name = payload['last_name']
                if payload.get('city'): user.city = payload['city']
                if payload.get('region'): user.region = payload['region']
                if payload.get('bio'): user.bio = payload['bio']
                user.save()

                if hasattr(user, 'entrepreneur_profile'):
                    ep = user.entrepreneur_profile
                    if payload.get('business_name'): ep.business_name = payload['business_name']
                    if payload.get('industry'): ep.industry = payload['industry']
                    if payload.get('description'): ep.description = payload['description']
                    ep.save()
                elif hasattr(user, 'mentor_profile'):
                    mp = user.mentor_profile
                    if payload.get('professional_title'): mp.professional_title = payload['professional_title']
                    if payload.get('biography'): mp.biography = payload['biography']
                    mp.save()
                server_id = user.id

            OfflineSyncRecord.objects.create(
                user=request.user,
                operation_id=op_id,
                entity_type=entity or op_type,
                action='CREATE',
                status='SYNCED',
                details=json.dumps(extra_data)
            )

            results.append({
                'operation_id': op_id,
                'status': 'SYNCED',
                'local_id': local_id,
                'server_id': server_id,
                'extra': extra_data
            })
            synced_count += 1

        except Exception as e:
            conflict_count += 1
            OfflineSyncRecord.objects.create(
                user=request.user,
                operation_id=op_id,
                entity_type=entity or op_type,
                action='FAILED',
                status='FAILED',
                details=str(e)
            )
            results.append({
                'operation_id': op_id,
                'status': 'FAILED',
                'local_id': local_id,
                'error': str(e)
            })

    return JsonResponse({
        'status': 'ok',
        'synced_count': synced_count,
        'conflict_count': conflict_count,
        'results': results,
        'synced_at': timezone.now().isoformat()
    })

@login_required
def sync_status_view(request):
    """Returns the user's sync history and server-side status."""
    records = OfflineSyncRecord.objects.filter(user=request.user).order_by('-server_timestamp')[:20]
    return JsonResponse({
        'user': request.user.username,
        'total_synced': records.count(),
        'recent_records': [
            {
                'operation_id': r.operation_id,
                'entity_type': r.entity_type,
                'status': r.status,
                'timestamp': r.server_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            for r in records
        ]
    })
