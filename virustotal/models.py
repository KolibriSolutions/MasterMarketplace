from django.db import models

class CheckedUrl(models.Model):
    check_status = (
        (1, 'OK'),
        (2, 'broken'),
        (3, 'malware')
    )

    URL = models.URLField()
    Status = models.IntegerField(choices=check_status)

    def __str__(self):
        return '{} : {}'.format(self.URL, self.Status)

# class CheckTask(models.Model):
#     Target = models.OneToOneField('projects.Project', related_name='checktask')
#     NumLeft = models.IntegerField(default=10)
