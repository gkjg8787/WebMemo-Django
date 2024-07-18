from datetime import datetime

from django.db import models
from django.contrib.auth.models import User


class MemoText(models.Model):
    # owner = models.ForeignKey(User,on_delete=models.CASCADE, related_name='memotext_owner')
    titleName = models.CharField(max_length=200, blank=True, null=True, default="")
    label = models.CharField(max_length=120, blank=True, null=True, default="")
    mainText = models.TextField(max_length=5000, blank=True, null=True, default="")
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        shortMainText = str(self.mainText)
        if len(self.mainText) > 32:
            shortMainText = shortMainText[:32]

        return (
            str(self.titleName)
            + ", "
            + str(self.label)
            + ", "
            + str(shortMainText)
            + ", "
            + str(self.created_at)
            + ", "
            + str(self.updated_at)
            # +' (' + str(self.owner) + ')'
        )
