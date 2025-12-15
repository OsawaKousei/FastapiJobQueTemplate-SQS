import unittest
from unittest.mock import Mock

from common.jobs.schemas import Job, JobRequest, JobStatus
from common.jobs.services import JobService
from common.shared.result import Failure, Success


class TestJobService(unittest.TestCase):
    def setUp(self):
        self.repository = Mock()
        self.queue = Mock()
        self.service = JobService(self.repository, self.queue)

    def test_create_job_success(self):
        request = JobRequest(payload="test_payload")

        # Mock repository.save to return the job (or just pass)
        self.repository.save.return_value = None

        result = self.service.create_job(request)

        self.assertIsInstance(result, Success)
        job = result.value
        self.assertEqual(job.payload, "test_payload")
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertIsNotNone(job.job_id)

        self.repository.save.assert_called_once()
        self.queue.send_message.assert_called_once_with(job.job_id)

    def test_create_job_failure_repo(self):
        request = JobRequest(payload="test_payload")

        # Mock repository.save to raise exception
        self.repository.save.side_effect = Exception("DB Error")

        result = self.service.create_job(request)

        self.assertIsInstance(result, Failure)
        self.assertIn("DB Error", str(result.error))

        self.queue.send_message.assert_not_called()

    def test_get_job_found(self):
        job_id = "test_id"
        job = Job(job_id=job_id, status=JobStatus.QUEUED, payload="payload")
        self.repository.get.return_value = job

        result = self.service.get_job(job_id)

        self.assertIsInstance(result, Success)
        self.assertEqual(result.value, job)

    def test_get_job_not_found(self):
        job_id = "test_id"
        self.repository.get.return_value = None

        result = self.service.get_job(job_id)

        self.assertIsInstance(result, Failure)
        self.assertEqual(result.error, "Job not found")
