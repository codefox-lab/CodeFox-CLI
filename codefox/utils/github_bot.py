import os
from github import Github


class GitHubBot:
    def __init__(self):
        self.github = Github(
            os.getenv("GITHUB_TOKEN")
        )

        self.repo = os.getenv('GITHUB_REPOSITORY')

    def send(self, message: str) -> None:
        pr_number = os.getenv('PR_NUMBER')
        if not pr_number:
            return

        repo = self.github.get_repo(
            self.repo
        )
        pr = repo.get_pull(int(pr_number))

        pr.create_issue_comment(message)