from common.config import get_settings
from common.infrastructure.aws.dynamodb import DynamoDBJobRepository
from common.jobs.schemas import Job, JobStatus


def test_save_and_get_job():
    settings = get_settings()
    repo = DynamoDBJobRepository(settings)

    job = Job(job_id="job_1", status=JobStatus.QUEUED, payload="payload_1")

    # Save
    saved_job = repo.save(job)
    assert saved_job == job

    # Get
    fetched_job = repo.get("job_1")
    assert fetched_job is not None
    assert fetched_job.job_id == "job_1"
    assert fetched_job.payload == "payload_1"
    assert fetched_job.status == JobStatus.QUEUED


def test_get_not_found():
    settings = get_settings()
    repo = DynamoDBJobRepository(settings)

    fetched_job = repo.get("non_existent")
    assert fetched_job is None


def test_update_status():
    settings = get_settings()
    repo = DynamoDBJobRepository(settings)

    job = Job(job_id="job_2", status=JobStatus.QUEUED, payload="payload_2")
    repo.save(job)

    # Update status
    repo.update_status("job_2", JobStatus.PROCESSING)

    fetched_job = repo.get("job_2")
    assert fetched_job.status == JobStatus.PROCESSING

    # Update status with result
    repo.update_status("job_2", JobStatus.COMPLETED, result="result_2")

    fetched_job = repo.get("job_2")
    assert fetched_job.status == JobStatus.COMPLETED
    assert fetched_job.result == "result_2"
