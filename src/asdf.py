from pathlib import Path
from dotenv import load_dotenv
import asyncio

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from ctutor_backend.tasks.executor import _execute_task_with_celery
from ctutor_backend.tasks import BaseTask, register_task, get_task_executor, TaskSubmission
from ctutor_backend.tasks.celery_app import get_celery_app

app = get_celery_app()

@register_task
class CalculateFactorialTask(BaseTask):
    @property
    def name(self) -> str:
        return "calculate_factorial"
    
    @property
    def timeout(self) -> int:
        return 60
    
    async def execute(self, number: int) -> dict:
        factorial = 1
        for i in range(1, number + 1):
            factorial *= i
            await asyncio.sleep(0.1)  # Simulate work
        
        return {
            "number": number,
            "factorial": factorial
        }

# Step 2: Create Celery wrapper
@app.task(bind=True, name='ctutor_backend.tasks.calculate_factorial')
def calculate_factorial_celery(self, **kwargs):
    return _execute_task_with_celery(self, CalculateFactorialTask, **kwargs)

# Step 3: Submit and get result
async def main():
    # Test the task directly
    task = CalculateFactorialTask()
    result = await task.execute(number=10)
    print(f"Direct execution result: {result}")
    print(f"10! = {result['factorial']}")
    
    # Also test the Celery task submission
    print("\nTesting Celery task submission...")
    executor = get_task_executor()
    
    # Submit example task
    submission = TaskSubmission(
        task_name="example_long_running",
        parameters={"duration": 2, "message": "Testing..."}
    )
    task_id = await executor.submit_task(submission)
    print(f"Example task submitted with ID: {task_id}")
    
    # Wait and get result
    result = await executor.get_task_result(task_id)
    print(f"Example result: {result}")
    
    if result and result.result:
        print(f"Example task completed: {result.result}")
    else:
        print("No result received")

if __name__ == "__main__":
    asyncio.run(main())