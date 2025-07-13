"""
CLI commands for managing task workers.
"""

import click
from ctutor_backend.tasks import get_task_executor

@click.group()
def worker():
    """Task worker management commands."""
    pass

@worker.command()
@click.option('--burst', is_flag=True, help='Exit after processing all jobs')
@click.option('--queues', default=None, help='Comma-separated list of queue names')
def start(burst: bool, queues: str):
    """
    Start a task worker to process queued jobs.
    
    Examples:
        ctutor worker start
        ctutor worker start --burst
        ctutor worker start --queues=high_priority,default
    """
    click.echo("Starting task worker...")
    
    # Parse queue names if provided
    queue_list = None
    if queues:
        queue_list = [q.strip() for q in queues.split(',')]
        click.echo(f"Processing queues: {queue_list}")
    
    # Import example tasks to register them
    try:
        from ctutor_backend.tasks.examples import (
            ExampleLongRunningTask,
            ExampleDataProcessingTask, 
            ExampleFailingTask
        )
        click.echo("Registered example tasks")
    except ImportError:
        click.echo("Warning: Could not import example tasks")
    
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
    """Show worker and queue status."""
    click.echo("Task Worker Status")
    click.echo("=================")
    
    try:
        task_executor = get_task_executor()
        
        # Check Redis connection
        task_executor.redis_client.ping()
        click.echo("✓ Redis connection: OK")
        
        # Show queue information
        queues = [
            ('High Priority', task_executor.high_priority_queue),
            ('Default', task_executor.default_queue),
            ('Low Priority', task_executor.low_priority_queue)
        ]
        
        click.echo("\nQueue Status:")
        for name, queue in queues:
            job_count = len(queue)
            click.echo(f"  {name}: {job_count} jobs")
            
    except Exception as e:
        click.echo(f"✗ Error checking status: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    worker()