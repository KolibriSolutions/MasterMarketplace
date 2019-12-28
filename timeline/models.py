from django.core.exceptions import ValidationError
from django.db import models


class Year(models.Model):
    """
    A Year is a college year
    """
    Name = models.CharField(max_length=250)
    Begin = models.DateField()
    End = models.DateField()

    def __str__(self):
        return self.Name

    def clean(self):
        if self.Begin is None or self.Begin is None:
            raise ValidationError("Please fill in a date, end date should be larger then begin date")
        if self.Begin > self.End:
            raise ValidationError("End date should be larger than begin date")

    class Meta:
        ordering = ["Begin"]
