import os
from urllib.parse import quote_plus

from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError, GitlabCreateError


class GitLabBot:
    def __init__(self) -> None:
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
        self.repository = os.getenv("GITLAB_REPOSITORY")
        self.mr_iid = os.getenv("PR_NUMBER")

        if not self.gitlab_token:
            raise ValueError(
                "GITLAB_TOKEN environment variable is not set. "
                "This token is required to authenticate with the GitLab API."
            )

        if not self.repository or not self.repository.isdigit():
            raise ValueError(f"Invalid GITLAB_REPOSITORY: {self.repository!r}")

        if not self.mr_iid or not self.mr_iid.isdigit():
            raise ValueError(
                f"Invalid PR_NUMBER value: {self.mr_iid!r}. "
                "Expected a numeric merge request IID."
            )

        self.gitlab = Gitlab(
            url=self.gitlab_url,
            private_token=self.gitlab_token,
        )

    def send(self, message: str) -> None:
        if not message or not message.strip():
            raise ValueError("Message must not be empty.")

       
        try:
            project = self.gitlab.projects.get(int(self.repository))
            mr = project.mergerequests.get(int(self.mr_iid))
            mr.notes.create({"body": message})
        except GitlabGetError as exc:
            raise RuntimeError(
                f"Failed to find project '{self.repository}' or merge request IID {self.mr_iid}."
            ) from exc
        except GitlabCreateError as exc:
            raise RuntimeError("Failed to create merge request note.") from exc
