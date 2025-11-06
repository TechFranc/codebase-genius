"""
Repository Mapper Module
Handles cloning, file tree generation, and README summarization
"""

import os
import shutil
import tempfile
from pathlib import Path
from git import Repo
from urllib.parse import urlparse
import llm_helper

# Directories to ignore
IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv',
    'env', '.env', 'dist', 'build', '.idea', '.vscode',
    'coverage', '.pytest_cache', '.mypy_cache', 'eggs',
    '.eggs', '*.egg-info', '.tox', '.coverage'
}

# File extensions to prioritize
IMPORTANT_EXTENSIONS = {
    '.py', '.jac', '.js', '.ts', '.java', '.cpp', '.c', '.h',
    '.go', '.rs', '.rb', '.php', '.md', '.txt', '.yaml', '.yml',
    '.json', '.toml'
}

def extract_repo_name(url):
    """Extract repository name from GitHub URL"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if path.endswith('.git'):
        path = path[:-4]
    return path.split('/')[-1]

def clone_repository(url, target_dir=None):
    """Clone a GitHub repository to local directory"""
    if target_dir is None:
        target_dir = tempfile.mkdtemp(prefix='codebase_genius_')
    
    try:
        print(f"Cloning repository to: {target_dir}")
        Repo.clone_from(url, target_dir, depth=1)
        return target_dir
    except Exception as e:
        raise Exception(f"Failed to clone repository: {str(e)}")

def should_ignore(path, base_path):
    """Check if a path should be ignored"""
    rel_path = os.path.relpath(path, base_path)
    parts = Path(rel_path).parts
    
    # Check if any part of the path matches ignore patterns
    for part in parts:
        if part in IGNORE_DIRS or part.startswith('.'):
            return True
    
    return False

def generate_file_tree(repo_path, max_depth=5):
    """Generate a hierarchical file tree structure"""
    tree = {
        "name": os.path.basename(repo_path),
        "type": "directory",
        "path": ".",
        "children": []
    }
    
    def build_tree(current_path, depth=0):
        if depth > max_depth:
            return None
        
        items = []
        try:
            for item in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item)
                
                if should_ignore(item_path, repo_path):
                    continue
                
                rel_path = os.path.relpath(item_path, repo_path)
                
                if os.path.isdir(item_path):
                    node = {
                        "name": item,
                        "type": "directory",
                        "path": rel_path,
                        "children": []
                    }
                    children = build_tree(item_path, depth + 1)
                    if children:
                        node["children"] = children
                    items.append(node)
                else:
                    items.append({
                        "name": item,
                        "type": "file",
                        "path": rel_path,
                        "size": os.path.getsize(item_path)
                    })
        except PermissionError:
            pass
        
        return items
    
    tree["children"] = build_tree(repo_path)
    return tree

def find_readme(repo_path):
    """Find and read README file"""
    readme_names = ['README.md', 'README.txt', 'README', 'readme.md', 'Readme.md']
    
    for name in readme_names:
        readme_path = os.path.join(repo_path, name)
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading README: {e}")
                return ""
    
    return ""

def summarize_readme(readme_content):
    """Summarize README content using LLM"""
    if not readme_content or len(readme_content.strip()) < 50:
        return "No README found or README is too short."
    
    # Truncate if too long
    if len(readme_content) > 10000:
        readme_content = readme_content[:10000] + "...\n[Truncated]"
    
    prompt = f"""Analyze this README and provide a concise summary (3-5 sentences) covering:
1. What the project does
2. Main features or purpose
3. Key technologies used

README Content:
{readme_content}

Provide ONLY the summary, no additional commentary."""

    try:
        summary = llm_helper.call_llm(prompt)
        return summary.strip()
    except Exception as e:
        print(f"Error summarizing README: {e}")
        return "Error generating summary. " + readme_content[:500]

def get_important_files(repo_path, file_tree):
    """Identify important files to analyze"""
    important_files = []
    
    def traverse(node, path_prefix=""):
        if node["type"] == "file":
            file_path = node["path"]
            ext = os.path.splitext(file_path)[1]
            
            # Check if it's a file we care about
            if ext in IMPORTANT_EXTENSIONS:
                full_path = os.path.join(repo_path, file_path)
                
                # Get file size
                try:
                    size = os.path.getsize(full_path)
                    # Skip very large files (>1MB)
                    if size > 1_000_000:
                        return
                except:
                    return
                
                # Determine language
                language = "unknown"
                if ext == ".py":
                    language = "python"
                elif ext == ".jac":
                    language = "jac"
                elif ext in [".js", ".ts"]:
                    language = "javascript"
                elif ext in [".java"]:
                    language = "java"
                
                # Prioritize entry points
                priority = 0
                basename = os.path.basename(file_path).lower()
                if basename in ['main.py', 'app.py', '__init__.py', '__main__.py', 'main.jac']:
                    priority = 10
                elif basename.startswith('test_'):
                    priority = -1  # Lower priority for tests
                
                important_files.append({
                    "path": file_path,
                    "language": language,
                    "size": size,
                    "priority": priority
                })
        
        elif node["type"] == "directory":
            for child in node.get("children", []):
                traverse(child, node["path"])
    
    traverse(file_tree)
    
    # Sort by priority (higher first)
    important_files.sort(key=lambda x: x["priority"], reverse=True)
    
    return important_files

def clone_and_map(github_url):
    """Main function to clone repository and generate mapping"""
    repo_name = extract_repo_name(github_url)
    
    # Clone repository
    local_path = clone_repository(github_url)
    
    # Generate file tree
    file_tree = generate_file_tree(local_path)
    
    # Find and summarize README
    readme_content = find_readme(local_path)
    readme_summary = summarize_readme(readme_content)
    
    # Get important files
    important_files = get_important_files(local_path, file_tree)
    
    return {
        "name": repo_name,
        "local_path": local_path,
        "file_tree": file_tree,
        "readme_summary": readme_summary,
        "important_files": important_files[:50]  # Limit to top 50 files
    }