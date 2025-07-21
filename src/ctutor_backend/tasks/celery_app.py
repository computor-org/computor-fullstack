"""
Celery application configuration and initialization.
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Get Redis configuration from environment (for broker)
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

# Build Redis URL from components (for message broker)
if REDIS_PASSWORD:
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}'
else:
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

# Get PostgreSQL configuration from environment (for result backend)
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'codeability')

# Build PostgreSQL URL for result backend
POSTGRES_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# Use Redis for message broker, PostgreSQL for result backend
BROKER_URL = REDIS_URL
BACKEND_URL = f'db+{POSTGRES_URL}'

# Create Celery application
app = Celery(
    'ctutor_backend',
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=['ctutor_backend.tasks.examples', 'ctutor_backend.tasks.student_testing', 'ctutor_backend.tasks.student_testing_advanced', 'ctutor_backend.tasks.system', 'ctutor_backend.tasks.hierarchy_management']
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minute soft limit
    task_acks_late=True,
    
    # Result settings
    result_serializer='json',
    result_expires=86400,  # Results expire after 1 day
    result_backend_transport_options={
        'visibility_timeout': 3600,
    },
    
    # Database result backend settings
    database_short_lived_sessions=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_disable_rate_limits=False,
    
    # Queue configuration with priorities
    task_default_queue='default',
    task_default_exchange='tasks',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
    
    # Define queues with priorities
    task_queues=(
        Queue('high_priority', Exchange('tasks'), routing_key='high_priority',
              queue_arguments={'x-max-priority': 10}),
        Queue('default', Exchange('tasks'), routing_key='default',
              queue_arguments={'x-max-priority': 5}),
        Queue('low_priority', Exchange('tasks'), routing_key='low_priority',
              queue_arguments={'x-max-priority': 1}),
    ),
    
    # Route tasks to queues based on priority
    task_routes={
        'ctutor_backend.tasks.student_testing.*': {
            'queue': 'high_priority',
            'routing_key': 'high_priority',
        },
        'ctutor_backend.tasks.examples.ExampleLongRunningTask': {
            'queue': 'default',
            'routing_key': 'default',
        },
        # Default routing for unspecified tasks
        '*': {
            'queue': 'default',
            'routing_key': 'default',
        }
    },
    
    # Beat scheduler configuration (if needed)
    beat_schedule={
        # Example periodic task
        # 'cleanup-old-results': {
        #     'task': 'ctutor_backend.tasks.cleanup.cleanup_old_results',
        #     'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        # },
    },
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
)

# Configure Celery to use JSON for serialization
app.conf.accept_content = ['json']
app.conf.result_accept_content = ['json']

# Import tasks to register them
def get_celery_app():
    """Get the configured Celery application instance."""
    return app