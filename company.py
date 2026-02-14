from abc import ABC, abstractmethod
from typing import Any

class Company(ABC):

    def __init__(self, name: str, slug: str | None = None):
        self.name = name
        self.slug = (slug or name.lower().replace(" ", "_")).strip()
        self.job_board_payload: Any = None

    @abstractmethod
    def fetch_raw_jobs(self) -> list[Any]:
        """
        Fetch raw job listings from the board (API response, HTML, etc.).
        Return a list of opaque items; parse_job() will interpret each.
        """
        pass

    @abstractmethod
    def parse_job(self, raw: Any) -> dict:
        """
        Turn one raw item into a job dict with at least:
          - title: str
          - url: str
          - meta: str (e.g. location | department | type)
          - skill_bullets: list[str]
          - qualification_bullets: list[str]
          - profile_lines: list[str]  (intro/profile paragraph lines)
        """
        pass

    def get_jobs(self) -> list[dict]:
        """Fetch and parse all jobs. Caller can then assign ids and write CSVs."""
        raw_list = self.fetch_raw_jobs()
        jobs = []
        for raw in raw_list:
            try:
                job = self.parse_job(raw)
                job["company"] = self.slug
                jobs.append(job)
            except Exception as e:
                # Log and skip bad entries
                print(f"[{self.slug}] skip job: {e}")
        return jobs
