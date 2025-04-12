import argparse
import os
from config import load_config
from git_commands import is_git_repo
from stats_processor import StatsProcessor
from models import ProjectStats

def process_repository(folder: str, stats_processor: StatsProcessor) -> ProjectStats:
    # Get project name from the last part of the folder path
    project_name = os.path.basename(os.path.normpath(folder))
    
    print(f"\n=== Processing Project {project_name} ===")
    print(f"Project path: {folder}")
    print(f"Current user: {stats_processor.current_user}")
    
    # Get summary statistics
    summary = stats_processor.get_summary_stats()
    print(f"\nSummary Statistics:")
    print(f"{summary.files_changed} files, +{summary.insertions}/-{summary.deletions} lines")
    
    # Get detailed statistics
    print("\nDetailed Statistics:")
    detailed = stats_processor.get_detailed_stats()
    for msg, data in detailed.items():
        print(f"{msg:<40} ｜ {data.commits:2d} commits ｜ +{data.insertions} / -{data.deletions} | {data.authors}")
        # Print files in a bulleted list with indentation
        for file in data.files:
            print(f"    • {file}")
        print()  # Add blank line between entries
# 
    # Create and return ProjectStats object
    return ProjectStats(
        project_name=project_name,
        folder_path=folder,
        current_user=stats_processor.current_user,
        summary=summary,
        detailed=detailed
    )

def process_directory(folder: str, stats_processor: StatsProcessor) -> list[ProjectStats]:
    results = []
    
    # Check if current directory is a git repo
    if is_git_repo(folder):
        try:
            os.chdir(folder)
            stats = process_repository(folder, stats_processor)
            results.append(stats)
        finally:
            os.chdir(os.path.dirname(folder))
    else:
        # If not a git repo, check subdirectories
        try:
            subdirs = [os.path.join(folder, d) for d in os.listdir(folder) 
                      if os.path.isdir(os.path.join(folder, d))]
            for subdir in subdirs:
                results.extend(process_directory(subdir, stats_processor))
        except PermissionError:
            print(f"\nSkipping {folder} - permission denied")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Git statistics generator')
    parser.add_argument('--since', default='yesterday', help='Start date')
    parser.add_argument('--until', default='today', help='End date')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    
    args = parser.parse_args()
    config = load_config(args.config)
    stats_processor = StatsProcessor(args.since, args.until)
    
    original_dir = os.getcwd()
    project_stats_list = []
    
    for folder in config['folders']:
        if not os.path.exists(folder):
            print(f"\nSkipping {folder} - folder does not exist")
            continue
        
        try:
            folder = os.path.abspath(folder)
            project_stats_list.extend(process_directory(folder, stats_processor))
        finally:
            os.chdir(original_dir)
    
    return project_stats_list

if __name__ == "__main__":
    main() 
