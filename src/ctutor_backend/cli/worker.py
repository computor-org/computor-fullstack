"""
CLI commands for managing Celery task workers.
"""

import click
import json
from ctutor_backend.tasks import get_task_executor
from ctutor_backend.cli.auth import authenticate, get_custom_client
from ctutor_backend.cli.config import CLIAuthConfig
from ctutor_backend.cli.crud import handle_api_exceptions

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

@worker.command()
@click.option('--task', default='example_long_running', help='Task name to run')
@click.option('--duration', default=5, help='Duration for long running tasks (seconds)')
@click.option('--priority', default=5, help='Task priority (0-10)')
@click.option('--wait', is_flag=True, help='Wait for task completion and show result')
@authenticate
@handle_api_exceptions
def test_job(auth: CLIAuthConfig, task: str, duration: int, priority: int, wait: bool):
    """
    Submit a test job to the task queue via API.
    
    This command will create the PostgreSQL tables if they don't exist.
    Requires authentication to access the task API.
    
    Examples:
        ctutor worker test-job
        ctutor worker test-job --task=example_long_running --duration=10
        ctutor worker test-job --wait
    """
    click.echo(f"Submitting test job: {task}")
    click.echo(f"Duration: {duration}s, Priority: {priority}")
    
    try:
        # Create task submission payload
        if task == 'example_long_running':
            parameters = {"duration": duration, "message": "CLI test job"}
        elif task == 'example_data_processing':
            parameters = {"processing_type": "basic", "data_size": 100}
        elif task == 'example_failing':
            parameters = {"should_fail": False}
        else:
            parameters = {}
        
        task_data = {
            "task_name": task,
            "parameters": parameters,
            "priority": priority
        }
        
        # Submit task via API
        client = get_custom_client(auth)
        response = client.create("tasks/submit", task_data)
        
        task_id = response.get("task_id")
        click.echo(f"✓ Task submitted successfully!")
        click.echo(f"  Task ID: {task_id}")
        
        if wait and task_id:
            click.echo("⏳ Waiting for task completion...")
            
            # Poll for completion
            import time
            max_wait = 60  # Maximum wait time in seconds
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    result_response = client.get(f"tasks/{task_id}/result")
                    status = result_response.get("status")
                    
                    if status in ["SUCCESS", "FAILURE"]:
                        click.echo(f"✓ Task completed!")
                        click.echo(f"  Status: {status}")
                        
                        if status == "SUCCESS" and "result" in result_response:
                            result_data = result_response["result"]
                            click.echo(f"  Result: {json.dumps(result_data, indent=2)}")
                        elif status == "FAILURE" and "error" in result_response:
                            click.echo(f"  Error: {result_response['error']}")
                        break
                        
                    elif status in ["PENDING", "STARTED"]:
                        click.echo(f"  Status: {status}...")
                        time.sleep(2)
                        elapsed += 2
                    else:
                        click.echo(f"  Unknown status: {status}")
                        break
                        
                except Exception as e:
                    click.echo(f"  Error checking status: {str(e)}")
                    break
            
            if elapsed >= max_wait:
                click.echo(f"⏱️  Task still running after {max_wait}s, stopped waiting")
                
        else:
            click.echo("💡 Use 'ctutor worker status' to check progress")
            click.echo("💡 Use '--wait' flag to wait for completion")
        
        # Show database info
        click.echo(f"\n📊 Task data stored in PostgreSQL:")
        click.echo(f"   Database: codeability")
        click.echo(f"   Table: celery_taskmeta") 
        if task_id:
            click.echo(f"   Query: SELECT * FROM celery_taskmeta WHERE task_id = '{task_id}';")
        
    except Exception as e:
        click.echo(f"✗ Error submitting test job: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    worker()