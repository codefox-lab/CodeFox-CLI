import os
from urllib.parse import quote_plus

from gitlab import Gitlab
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError, GitlabCreateError


class GitLabBot:
    def __init__(self) -> None:
        self.gitlab_token = os.getenv("GITLAB_BOT")
        self.gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
        self.repository = os.getenv("GITLAB_REPOSITORY")
        self.mr_iid = os.getenv("PR_NUMBER")

        if not self.gitlab_token:
            raise ValueError(
                "GITLAB_BOT environment variable is not set. "
                "This token is required to authenticate with the GitLab API."
            )

        if not self.repository:
            raise ValueError(
                "GITLAB_REPOSITORY environment variable is not set. "
                "Expected format: 'group/project' or 'group/subgroup/project'."
            )

        if not self.mr_iid or not self.mr_iid.isdigit():
            raise ValueError(
                f"Invalid PR_NUMBER value: {self.mr_iid!r}. "
                "Expected a numeric merge request IID."
            )

        self.gitlab = Gitlab(
            url=self.gitlab_url,
            private_token=self.gitlab_token,
        )

        try:
            self.gitlab.auth()
        except GitlabAuthenticationError as exc:
            raise RuntimeError("Failed to authenticate to GitLab API.") from exc

    def send(self, message: str) -> None:
        if not message or not message.strip():
            raise ValueError("Message must not be empty.")

        project_path = quote_plus(self.repository)

        try:
            project = self.gitlab.projects.get(project_path)
            mr = project.mergerequests.get(int(self.mr_iid))
            mr.notes.create({"body": message})
        except GitlabGetError as exc:
            raise RuntimeError(
                f"Failed to find project '{self.repository}' or merge request IID {self.mr_iid}."
            ) from exc
        except GitlabCreateError as exc:
            raise RuntimeError("Failed to create merge request note.") from exc
