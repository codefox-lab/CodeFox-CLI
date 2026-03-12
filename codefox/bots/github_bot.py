import os

from github import Github


class GitHubBot:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repository = os.getenv("GITHUB_REPOSITORY")
        self.pr_number = os.getenv("PR_NUMBER")

        if not self.github_token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is not set. "
                "This token is required to authenticate with the GitHub API."
            )

        if not self.repository:
            raise ValueError(
                "GITHUB_REPOSITORY environment variable is not set. "
                "Expected format: 'owner/repository'."
            )

        self.github = Github(self.github_token)

    def send(self, message: str) -> None:
        if not self.pr_number or not self.pr_number.isdigit():
            raise RuntimeError(f"Invalid PR_NUMBER: {self.pr_number}")

        repo = self.github.get_repo(self.repository)
        pr = repo.get_pull(int(self.pr_number))

        pr.create_issue_comment(message)
