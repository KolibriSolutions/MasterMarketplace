from django.apps import AppConfig
from filelock import FileLock

class ProjectsConfig(AppConfig):
    name = 'projects'

    def ready(self):
        from .models import Project
        f = FileLock()
        if f.lock('startup'):
            for p in Project.objects.all():
                p.test_links()
            f.unlock('startup')