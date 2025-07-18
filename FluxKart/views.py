from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db import transaction, IntegrityError
import json

from .models import Contact

@csrf_exempt
def identify(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    try:
        data = json.loads(request.body)
        phone = data.get('phoneNumber')
        email = data.get('email')

        if not phone and not email:
            return JsonResponse({'error': 'phoneNumber or email is required'}, status=400)
        for _ in range(2):
            try:
                with transaction.atomic():
                    matching_contacts = Contact.objects.filter(
                        Q(email=email) | Q(phoneNumber=phone)
                    ).order_by('createdAt')
                    
                    if not matching_contacts.exists():
                        new_contact = Contact.objects.create(
                            email=email,
                            phoneNumber=phone,
                            linkPrecedence='primary'
                        )
                        return JsonResponse({
                            "contact": {
                                "primaryContactId": new_contact.id,
                                "emails": [email] if email else [],
                                "phoneNumbers": [phone] if phone else [],
                                "secondaryContactIds": []
                            }
                        })
                        
                    primary = None
                    for contact in matching_contacts:
                        if contact.linkPrecedence == 'primary':
                            primary = contact
                            break
                    if not primary:
                        secondary_contact = matching_contacts.first()
                        if secondary_contact.linkPrecedence == 'secondary':
                            primary = Contact.objects.get(id=secondary_contact.linkedId)
                        else:
                            primary = secondary_contact

                    for contact in matching_contacts:
                        if contact.linkPrecedence == 'primary' and contact.id != primary.id:
                            contact.linkPrecedence = 'secondary'
                            contact.linkedId = primary.id
                            contact.save()
                            
                    known_emails = set(c.email for c in matching_contacts if c.email)
                    known_phones = set(c.phoneNumber for c in matching_contacts if c.phoneNumber)
                    
                    needs_new_row = False
                    if email and email not in known_emails:
                        needs_new_row = True
                    if phone and phone not in known_phones:
                        needs_new_row = True
                        
                    if needs_new_row:
                        Contact.objects.create(
                            email=email,
                            phoneNumber=phone,
                            linkedId=primary.id,
                            linkPrecedence='secondary'
                        )
                    
                    all_contacts = Contact.objects.filter(
                        Q(id=primary.id) | Q(linkedId=primary.id)
                    )

                    emails = sorted(set(c.email for c in all_contacts if c.email))
                    phones = sorted(set(c.phoneNumber for c in all_contacts if c.phoneNumber))
                    secondary_ids = sorted(c.id for c in all_contacts if c.linkPrecedence == 'secondary')
                    
                    return JsonResponse({
                        "contact": {
                            "primaryContactId": primary.id,
                            "emails": emails,
                            "phoneNumbers": phones,
                            "secondaryContactIds": secondary_ids
                        }
                    })
            except IntegrityError:
                continue
        return JsonResponse({'error': 'Something went wrong'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
