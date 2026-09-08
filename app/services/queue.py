"""Redis-backed boundary between request handling and untrusted execution."""
import json

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class SubmissionQueue:
    def __init__(self, client: Redis | None = None):
        self.client = client or Redis.from_url(settings.redis_url, decode_responses=True)

    def enqueue(self, submission_id: int) -> None:
        try:
            self.client.lpush(settings.submission_queue_name, json.dumps({"submission_id": submission_id}))
        except RedisError as error:
            raise RuntimeError("Submission queue is unavailable") from error

    def dequeue(self, timeout_seconds: int = 5) -> int | None:
        try:
            item = self.client.brpop(settings.submission_queue_name, timeout=timeout_seconds)
        except RedisError as error:
            raise RuntimeError("Submission queue is unavailable") from error
        if not item:
            return None
        _, payload = item
        return int(json.loads(payload)["submission_id"])
