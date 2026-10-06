from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):

    TYPE_CHOICES = (
        ('order', 'Order'),
        ('payment', 'Payment'),
        ('shipping', 'Shipping'),
        ('general', 'General'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='general'
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.type}"