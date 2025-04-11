import argparse
import subprocess
import yaml
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List
import os

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

def load_config(config_path: str = "config.yaml") -> Dict:
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"folders": ["."]}  # Default to current directory

def run_git_command(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return ""

def get_summary_stats(since: str, until: str) -> CommitSummary:
    command = f"""git log --since="{since}" --until="{until}" --shortstat | \
        awk '/files changed/{{files+=$1; ins+=$4; del+=$6}} END{{print files" "ins" "del}}'"""
    
    output = run_git_command(command)
    if not output:
        return CommitSummary(0, 0, 0)
    
    try:
        files, ins, dels = map(int, output.split())
        return CommitSummary(files, ins, dels)
    except ValueError:
        return CommitSummary(0, 0, 0)

def get_detailed_stats(since: str, until: str) -> Dict[str, DetailedCommit]:
    command = f"""git log --all --since="{since}" --until="{until}" --numstat \
        --pretty=format:'@@@%s|%an' --date=iso-strict"""
    
    output = run_git_command(command)
    commits_data = {}
    
    current_msg = None
    for line in output.splitlines():
        if line.startswith('@@@'):
            # Handle commit header
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
            # Handle stat line
            parts = line.split()
            if len(parts) == 3 and parts[0] != '-':
                commits_data[current_msg].insertions += int(parts[0])
                commits_data[current_msg].deletions += int(parts[1])
                if parts[2] not in commits_data[current_msg].files:
                    commits_data[current_msg].files.append(parts[2])
    
    return commits_data

def is_git_repo(path: str) -> bool:
    """Check if the given path is a git repository."""
    command = "git rev-parse --is-inside-work-tree"
    original_dir = os.getcwd()
    try:
        os.chdir(path)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False
    finally:
        os.chdir(original_dir)

def main():
    parser = argparse.ArgumentParser(description='Git statistics generator')
    parser.add_argument('--since', default='yesterday', help='Start date')
    parser.add_argument('--until', default='today', help='End date')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    original_dir = os.getcwd()
    
    for folder in config['folders']:
        if not os.path.exists(folder):
            print(f"\nSkipping {folder} - folder does not exist")
            continue
            
        if not is_git_repo(folder):
            print(f"\nSkipping {folder} - not a git repository")
            continue
            
        print(f"\n=== Processing {folder} ===")
        
        try:
            os.chdir(folder)
            
            # Get summary statistics
            summary = get_summary_stats(args.since, args.until)
            print(f"\nSummary Statistics:")
            print(f"{summary.files_changed} files, +{summary.insertions}/-{summary.deletions} lines")
            
            # Get detailed statistics
            print("\nDetailed Statistics:")
            detailed = get_detailed_stats(args.since, args.until)
            for msg, data in detailed.items():
                authors_str = ','.join(data.authors)
                files_str = ','.join(data.files)
                print(f"{msg:<40} ｜ {data.commits:2d} commits ｜ +{data.insertions} / -{data.deletions} | {authors_str} ｜ {files_str}")
                
        finally:
            os.chdir(original_dir)

if __name__ == "__main__":
    main() 