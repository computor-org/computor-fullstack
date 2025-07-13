"""
CLI commands for managing Celery task workers.
"""

import click
from ctutor_backend.tasks import get_task_executor

@click.group()
def worker():
    """Celery task worker management commands."""
    pass

@worker.command()
@click.option('--burst', is_flag=True, help='Exit after processing all jobs')
@click.option('--queues', default=None, help='Comma-separated list of queue names')
def start(burst: bool, queues: str):
    """
    Start a Celery worker to process queued jobs.
    
    Examples:
        ctutor worker start
        ctutor worker start --burst
        ctutor worker start --queues=high_priority,default
    """
    click.echo("Starting Celery task worker...")
    
    # Parse queue names if provided
    queue_list = None
    if queues:
        queue_list = [q.strip() for q in queues.split(',')]
        click.echo(f"Processing queues: {queue_list}")
    else:
        click.echo("Processing all queues: high_priority, default, low_priority")
    
    # Import example tasks to register them
    try:
        from ctutor_backend.tasks.examples import (
            example_long_running_celery_task,
            example_data_processing_celery_task,
            example_failing_celery_task
        )
        click.echo("Registered example tasks with Celery")
    except ImportError as e:
        click.echo(f"Warning: Could not import example tasks: {e}")
    
    # Start worker
    task_executor = get_task_executor()
    
    if burst:
        click.echo("Running in burst mode (will exit after processing all jobs)")
    
    try:
        task_executor.start_worker(queues=queue_list, burst=burst)
    except KeyboardInterrupt:
        click.echo("\nWorker stopped by user")
    except Exception as e:
        click.echo(f"Worker error: {str(e)}")
        raise click.ClickException(str(e))

@worker.command()
def status():
    """Show Celery worker and queue status."""
    click.echo("Celery Task Worker Status")
    click.echo("========================")
    
    try:
        task_executor = get_task_executor()
        status_info = task_executor.get_worker_status()
        
        # Show connection status
        if status_info['status'] == 'connected':
            click.echo("✓ Celery broker connection: OK")
        elif status_info['status'] == 'error':
            click.echo(f"✗ Celery broker connection: ERROR - {status_info.get('error', 'Unknown')}")
        else:
            click.echo(f"? Celery broker connection: {status_info['status']}")
        
        # Show broker URL
        click.echo(f"  Broker: {status_info['broker_url']}")
        
        # Show worker information  
        workers = status_info['workers']
        click.echo(f"\nActive Workers: {workers['active_count']}")
        
        if workers['workers']:
            for worker_name, tasks in workers['workers'].items():
                click.echo(f"  {worker_name}: {len(tasks)} active tasks")
        elif workers['active_count'] == 0:
            click.echo("  No active workers found")
        
        # Show queue information
        click.echo("\nQueue Status:")
        queues = status_info['queues']
        for queue_name in ['high_priority', 'default', 'low_priority']:
            count = queues.get(queue_name, 'unknown')
            display_name = queue_name.replace('_', ' ').title()
            if isinstance(count, int):
                click.echo(f"  {display_name}: {count} jobs")
            else:
                click.echo(f"  {display_name}: {count}")
            
    except Exception as e:
        click.echo(f"✗ Error checking status: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    worker()