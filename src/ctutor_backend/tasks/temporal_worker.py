"""
Temporal worker implementation for running workflows and activities.
"""

import asyncio
import os
import signal
from typing import List, Optional
from temporalio.worker import Worker
from temporalio.client import Client

from .temporal_client import (
    get_temporal_client,
    DEFAULT_TASK_QUEUE
)

# Import all workflows and activities
from .temporal_examples import (
    ExampleLongRunningWorkflow,
    ExampleDataProcessingWorkflow,
    ExampleErrorHandlingWorkflow,
    simulate_processing_activity,
    process_data_chunk_activity
)
from .temporal_student_testing import (
    StudentTestingWorkflow,
    SubmissionProcessingWorkflow,
    clone_repository_activity,
    execute_tests_activity,
    commit_test_results_activity
)
from .temporal_system import (
    ReleaseStudentsWorkflow,
    ReleaseCourseWorkflow,
    release_students_activity,
    release_course_activity
)
from .temporal_hierarchy_management import (
    CreateOrganizationWorkflow,
    CreateCourseFamilyWorkflow,
    CreateCourseWorkflow,
    create_organization_activity,
    create_course_family_activity,
    create_course_activity
)


class TemporalWorker:
    """Temporal worker for executing workflows and activities."""
    
    def __init__(self, task_queues: Optional[List[str]] = None):
        """
        Initialize the worker.
        
        Args:
            task_queues: List of task queues to listen on. If None, listens on all queues.
        """
        self.task_queues = task_queues or [
            DEFAULT_TASK_QUEUE,
            "computor-high-priority",
            "computor-low-priority"
        ]
        self.workers: List[Worker] = []
        self.client: Optional[Client] = None
        self._shutdown = False
    
    async def start(self):
        """Start the worker and begin processing workflows."""
        print(f"Starting Temporal worker for queues: {', '.join(self.task_queues)}")
        
        # Get client
        self.client = await get_temporal_client()
        
        # Define workflows and activities
        workflows = [
            ExampleLongRunningWorkflow,
            ExampleDataProcessingWorkflow,
            ExampleErrorHandlingWorkflow,
            StudentTestingWorkflow,
            SubmissionProcessingWorkflow,
            ReleaseStudentsWorkflow,
            ReleaseCourseWorkflow,
            CreateOrganizationWorkflow,
            CreateCourseFamilyWorkflow,
            CreateCourseWorkflow,
        ]
        
        activities = [
            simulate_processing_activity,
            process_data_chunk_activity,
            clone_repository_activity,
            execute_tests_activity,
            commit_test_results_activity,
            release_students_activity,
            release_course_activity,
            create_organization_activity,
            create_course_family_activity,
            create_course_activity,
        ]
        
        # Create a worker for each task queue
        for task_queue in self.task_queues:
            worker = Worker(
                self.client,
                task_queue=task_queue,
                workflows=workflows,
                activities=activities,
            )
            self.workers.append(worker)
            print(f"Created worker for queue: {task_queue}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Run all workers concurrently
        try:
            await asyncio.gather(*[worker.run() for worker in self.workers])
        except asyncio.CancelledError:
            print("Workers cancelled")
        finally:
            await self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down workers...")
        self._shutdown = True
        # Cancel all worker tasks
        for worker in self.workers:
            asyncio.create_task(worker.shutdown())
    
    async def shutdown(self):
        """Shutdown the worker gracefully."""
        print("Shutting down Temporal workers...")
        
        # Workers are already shutting down from signal handler
        # Just wait a bit for graceful shutdown
        await asyncio.sleep(1)
        
        # Close client connection
        if self.client:
            await self.client.close()
        
        print("Workers shut down successfully")


async def run_worker(queues: Optional[List[str]] = None):
    """
    Run a Temporal worker.
    
    Args:
        queues: Optional list of queue names to process
    """
    worker = TemporalWorker(task_queues=queues)
    await worker.start()


def main():
    """Main entry point for running a worker from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Temporal worker")
    parser.add_argument(
        "--queues",
        nargs="+",
        help="Task queues to process (default: all queues)",
        default=None
    )
    parser.add_argument(
        "--high-priority",
        action="store_true",
        help="Process only high priority queue"
    )
    parser.add_argument(
        "--default",
        action="store_true", 
        help="Process only default queue"
    )
    parser.add_argument(
        "--low-priority",
        action="store_true",
        help="Process only low priority queue"
    )
    
    args = parser.parse_args()
    
    # Determine queues
    queues = None
    if args.queues:
        queues = args.queues
    elif args.high_priority:
        queues = ["computor-high-priority"]
    elif args.default:
        queues = [DEFAULT_TASK_QUEUE]
    elif args.low_priority:
        queues = ["computor-low-priority"]
    
    # Run worker
    asyncio.run(run_worker(queues))


if __name__ == "__main__":
    main()