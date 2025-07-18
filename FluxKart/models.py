from django.db import models

class Contact(models.Model):
    phoneNumber = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    email = models.EmailField(null=True, blank=True, db_index=True)
    linkedId = models.IntegerField(null=True, blank=True)  # points to primary contact
    linkPrecedence = models.CharField(
        max_length=10,
        choices=[('primary', 'primary'), ('secondary', 'secondary')],
        default='primary'
    )
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    deletedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phoneNumber']),
        ]
