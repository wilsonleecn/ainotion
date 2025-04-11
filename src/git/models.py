from dataclasses import dataclass
from typing import List, Dict

@dataclass
class CommitSummary:
    files_changed: int
    insertions: int
    deletions: int

@dataclass
class DetailedCommit:
    commits: int
    insertions: int
    deletions: int
    authors: List[str]
    files: List[str]

@dataclass
class ProjectStats:
    project_name: str
    folder_path: str
    current_user: str
    summary: CommitSummary
    detailed: Dict[str, DetailedCommit] 