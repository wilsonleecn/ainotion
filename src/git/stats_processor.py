from models import CommitSummary, DetailedCommit
from git_commands import run_git_command
from typing import Dict

class StatsProcessor:
    def __init__(self, since: str, until: str):
        self.since = since
        self.until = until
        self.current_user = self._get_current_user()

    def _get_current_user(self) -> str:
        command = "git config user.name"
        return run_git_command(command).strip()

    def get_summary_stats(self) -> CommitSummary:
        command = f"""git log --since="{self.since}" --until="{self.until}" --author="{self.current_user}" --shortstat | \
            awk '/files changed/{{files+=$1; ins+=$4; del+=$6}} END{{print files" "ins" "del}}'"""
        
        output = run_git_command(command)
        if not output:
            return CommitSummary(0, 0, 0)
        
        try:
            files, ins, dels = map(int, output.split())
            return CommitSummary(files, ins, dels)
        except ValueError:
            return CommitSummary(0, 0, 0)

    def get_detailed_stats(self) -> Dict[str, DetailedCommit]:
        command = f"""git log --all --since="{self.since}" --until="{self.until}" --author="{self.current_user}" --numstat \
            --pretty=format:'@@@%s|%an' --date=iso-strict"""
        
        output = run_git_command(command)
        commits_data = {}
        
        current_msg = None
        for line in output.splitlines():
            if line.startswith('@@@'):
                msg, author = line[3:].split('|')
                current_msg = msg
                if current_msg not in commits_data:
                    commits_data[current_msg] = DetailedCommit(
                        commits=0,
                        insertions=0,
                        deletions=0,
                        authors=[],
                        files=[]
                    )
                commits_data[current_msg].commits += 1
                if author not in commits_data[current_msg].authors:
                    commits_data[current_msg].authors.append(author)
            
            elif current_msg and line.strip():
                parts = line.split()
                if len(parts) == 3 and parts[0] != '-':
                    commits_data[current_msg].insertions += int(parts[0])
                    commits_data[current_msg].deletions += int(parts[1])
                    if parts[2] not in commits_data[current_msg].files:
                        commits_data[current_msg].files.append(parts[2])
        
        return commits_data 