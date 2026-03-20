import os

from gitlab import Gitlab


class GitLabBot:
    def __init__(self):
        self.gitlab_token = os.getenv("GITLAB_BOT")
        self.gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com/")
        self.repository = os.getenv("GITLAB_REPOSITORY")
        self.pr_number = os.getenv("PR_NUMBER")

        if not self.gitlab_token:
            raise ValueError(
                "GITLAB_BOT environment variable is not set. "
                "This token is required to authenticate with the Gitlab API."
            )

        if not self.repository:
            raise ValueError(
                "GITLAB_REPOSITORY environment variable is not set. "
                "Expected format: 'owner/repository'."
            )

        self.gitlab = Gitlab(
            url=self.gitlab_url,
            private_token=self.gitlab_token
        )

    def send(self, message: str) -> None:
        if not self.pr_number or not self.pr_number.isdigit():
            raise RuntimeError(f"Invalid PR_NUMBER: {self.pr_number}")

        repo = self.gitlab.projects.get(self.repository)
        mr = repo.mergerequests.get(int(self.pr_number))

        mr.notes.create({"body": message})
