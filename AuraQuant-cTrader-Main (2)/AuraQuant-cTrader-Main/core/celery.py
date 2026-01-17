
import os
from celery import Celery

# Define as configurações do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('birdstone')

# Carrega as configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir automaticamente as tarefas em todos os apps Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
