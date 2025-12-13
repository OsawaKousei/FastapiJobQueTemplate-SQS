import boto3
from typing import Optional
from app.src.domain.jobs.repository import JobRepository
from app.src.domain.jobs.schemas import Job, JobStatus
from app.src.config import Settings

class DynamoDBJobRepository(JobRepository):
    def __init__(self, settings: Settings):
        self.table_name = settings.table_name
        self.dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=settings.aws_endpoint_url,
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.table = self.dynamodb.Table(self.table_name)

    def save(self, job: Job) -> Job:
        item = job.model_dump()
        # Enum to string
        item['status'] = item['status'].value
        self.table.put_item(Item=item)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        response = self.table.get_item(Key={'job_id': job_id})
        if 'Item' not in response:
            return None
        item = response['Item']
        return Job(**item)

    def update_status(self, job_id: str, status: str, result: Optional[str] = None) -> None:
        update_expression = "set #st = :s"
        expression_attribute_names = {'#st': 'status'}
        expression_attribute_values = {':s': status}

        if result:
            update_expression += ", #r = :r"
            expression_attribute_names['#r'] = 'result'
            expression_attribute_values[':r'] = result

        self.table.update_item(
            Key={'job_id': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
