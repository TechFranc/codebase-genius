"""
Documentation Generator Module
Synthesizes comprehensive documentation from analyzed code

This module generates:
- Professional markdown documentation
- Mermaid architecture diagrams
- API reference documentation
- Code statistics and metrics
- Installation instructions
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import llm_helper

def generate_mermaid_class_diagram(entities: List[Dict[str, Any]]) -> str:
    """
    Generate Mermaid class diagram showing code structure
    
    Args:
        entities: List of code entities
        
    Returns:
        Mermaid diagram syntax as string
    """
    diagram_lines = ["```mermaid", "classDiagram"]
    
    # Group entities by file for better organization
    files = {}
    for entity in entities:
        file = entity.get("file_path", "unknown")
        if file not in files:
            files[file] = []
        files[file].append(entity)
    
    # Track which classes we've added
    added_classes = set()
    relationships = []
    
    # Add classes with their methods
    for file, ents in files.items():
        for entity in ents:
            if entity["type"] == "class":
                class_name = entity["name"].replace("-", "_")
                if class_name in added_classes:
                    continue
                    
                added_classes.add(class_name)
                diagram_lines.append(f"    class {class_name} {{")
                
                # Add methods
                methods = entity.get("dependencies", [])[:10]  # Limit to 10 methods
                for method in methods:
                    diagram_lines.append(f"        +{method}()")
                
                # Add attributes if available
                if "attributes" in entity:
                    for attr in entity["attributes"][:5]:  # Limit to 5 attributes
                        diagram_lines.append(f"        -{attr}")
                
                diagram_lines.append("    }")
                
                # Store inheritance relationships
                if "bases" in entity and entity["bases"]:
                    for base in entity["bases"]:
                        base_clean = base.replace("-", "_")
                        relationships.append(f"    {base_clean} <|-- {class_name}")
    
    # Add functions as separate classes
    for entity in entities[:15]:  # Limit to first 15 functions
        if entity["type"] == "function":
            func_name = entity["name"].replace("-", "_")
            if func_name in added_classes:
                continue
            
            added_classes.add(func_name)
            params = entity.get("parameters", [])
            param_str = ", ".join([p.get("name", str(p)) for p in params[:3]]) if isinstance(params, list) else ""
            
            diagram_lines.append(f"    class {func_name} {{")
            diagram_lines.append(f"        <<function>>")
            diagram_lines.append(f"        +execute({param_str})")
            diagram_lines.append("    }")
    
    # Add Jac-specific entities
    for entity in entities:
        if entity["type"] in ["walker", "node"]:
            name = entity["name"].replace("-", "_")
            if name in added_classes:
                continue
            
            added_classes.add(name)
            diagram_lines.append(f"    class {name} {{")
            diagram_lines.append(f"        <<{entity['type']}>>")
            
            # Add attributes for walkers/nodes
            if "attributes" in entity:
                for attr in entity["attributes"][:5]:
                    if isinstance(attr, tuple):
                        diagram_lines.append(f"        +{attr[0]} : {attr[1]}")
                    else:
                        diagram_lines.append(f"        +{attr}")
            
            diagram_lines.append("    }")
    
    # Add relationships
    diagram_lines.extend(relationships)
    
    diagram_lines.append("```")
    return "\n".join(diagram_lines)

def generate_mermaid_flow_diagram(entities: List[Dict[str, Any]]) -> str:
    """
    Generate Mermaid flow diagram showing workflow
    
    Args:
        entities: List of code entities
        
    Returns:
        Mermaid flowchart syntax as string
    """
    diagram_lines = ["```mermaid", "flowchart TD"]
    
    # Find walkers (main workflow components)
    walkers = [e for e in entities if e["type"] == "walker"]
    
    if walkers:
        for i, walker in enumerate(walkers[:5]):  # Limit to 5 walkers
            node_id = f"W{i}"
            diagram_lines.append(f"    {node_id}[{walker['name']}]")
            
            if i > 0:
                diagram_lines.append(f"    W{i-1} --> {node_id}")
    else:
        # Create a simple flow from functions
        functions = [e for e in entities if e["type"] == "function"][:5]
        for i, func in enumerate(functions):
            node_id = f"F{i}"
            diagram_lines.append(f"    {node_id}[{func['name']}]")
            
            if i > 0:
                diagram_lines.append(f"    F{i-1} --> {node_id}")
    
    diagram_lines.append("```")
    return "\n".join(diagram_lines)

def generate_file_tree_markdown(file_tree: Dict[str, Any], max_depth: int = 4) -> str:
    """
    Convert file tree to markdown format
    
    Args:
        file_tree: Hierarchical file tree structure
        max_depth: Maximum depth to display
        
    Returns:
        Markdown formatted file tree
    """
    lines = []
    
    def traverse(node, level=0, prefix=""):
        if level > max_depth:
            return
        
        indent = "  " * level
        
        if node["type"] == "directory":
            icon = "📁"
            lines.append(f"{indent}- {icon} **{node['name']}/**")
            
            for child in node.get("children", []):
                traverse(child, level + 1, indent + "  ")
        else:
            icon = "📄"
            size = node.get("size", 0)
            size_str = f" *({format_size(size)})*" if size > 0 else ""
            lines.append(f"{indent}- {icon} {node['name']}{size_str}")
    
    traverse(file_tree)
    return "\n".join(lines)

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}GB"

def group_entities_by_file(entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group entities by their source file
    
    Args:
        entities: List of code entities
        
    Returns:
        Dictionary mapping file paths to entities
    """
    grouped = {}
    for entity in entities:
        file = entity.get("file_path", "unknown")
        if file not in grouped:
            grouped[file] = []
        grouped[file].append(entity)
    return grouped

def generate_api_reference(entities: List[Dict[str, Any]]) -> str:
    """
    Generate comprehensive API reference documentation
    
    Args:
        entities: List of code entities
        
    Returns:
        Markdown formatted API reference
    """
    sections = []
    
    # Group by file
    by_file = group_entities_by_file(entities)
    
    for file_path, ents in sorted(by_file.items()):
        if not ents:
            continue
        
        sections.append(f"### 📄 `{file_path}`\n")
        
        # Classes first
        classes = [e for e in ents if e["type"] == "class"]
        if classes:
            sections.append("#### Classes\n")
            for entity in classes:
                name = entity["name"]
                docstring = entity.get("docstring", "No documentation available.")
                params = entity.get("parameters", [])
                
                sections.append(f"##### `class {name}`\n")
                
                if params:
                    sections.append(f"**Inherits from:** `{', '.join(params)}`\n")
                
                if docstring:
                    sections.append(f"{docstring}\n")
                
                # List methods with details
                methods = entity.get("methods", [])
                if methods:
                    sections.append("**Methods:**\n")
                    for method in methods[:15]:  # Limit to 15 methods
                        if isinstance(method, dict):
                            method_name = method.get('name', str(method))
                            decorators = []
                            if method.get('is_static'):
                                decorators.append('@staticmethod')
                            if method.get('is_class'):
                                decorators.append('@classmethod')
                            if method.get('is_property'):
                                decorators.append('@property')
                            
                            decorator_str = ' '.join(decorators) if decorators else ''
                            sections.append(f"- `{method_name}()` {decorator_str}")
                        else:
                            sections.append(f"- `{method}()`")
                    sections.append("")
                
                # List attributes
                attributes = entity.get("attributes", [])
                if attributes:
                    sections.append("**Attributes:**\n")
                    for attr in attributes[:10]:
                        sections.append(f"- `{attr}`")
                    sections.append("")
        
        # Functions
        functions = [e for e in ents if e["type"] == "function"]
        if functions:
            sections.append("#### Functions\n")
            for entity in functions:
                name = entity["name"]
                docstring = entity.get("docstring", "No documentation available.")
                params = entity.get("parameters", [])
                
                # Format parameters
                if params:
                    param_strs = []
                    for p in params:
                        if isinstance(p, dict):
                            param_name = p.get('name', str(p))
                            param_type = p.get('annotation', '')
                            if param_type:
                                param_strs.append(f"{param_name}: {param_type}")
                            else:
                                param_strs.append(param_name)
                        else:
                            param_strs.append(str(p))
                    param_str = ", ".join(param_strs)
                else:
                    param_str = ""
                
                # Add return type if available
                return_type = entity.get("return_type", "")
                return_str = f" -> {return_type}" if return_type else ""
                
                sections.append(f"##### `{name}({param_str}){return_str}`\n")
                
                # Add decorators
                decorators = entity.get("decorators", [])
                if decorators:
                    sections.append(f"**Decorators:** `{', '.join(decorators)}`\n")
                
                if docstring:
                    sections.append(f"{docstring}\n")
                
                # Add complexity info
                complexity = entity.get("complexity", 0)
                if complexity > 0:
                    sections.append(f"**Complexity:** {complexity}\n")
        
        # Jac-specific: Walkers and Nodes
        jac_entities = [e for e in ents if e["type"] in ["walker", "node", "edge", "ability"]]
        if jac_entities:
            sections.append("#### Jac Components\n")
            for entity in jac_entities:
                name = entity["name"]
                etype = entity["type"].title()
                line = entity.get('line_start', 'unknown')
                
                sections.append(f"##### {etype}: `{name}`\n")
                sections.append(f"*Defined at line {line}*\n")
                
                # Add attributes for walkers/nodes
                attributes = entity.get("attributes", [])
                if attributes:
                    sections.append("**Attributes:**\n")
                    for attr in attributes:
                        if isinstance(attr, tuple) and len(attr) >= 2:
                            sections.append(f"- `{attr[0]}`: `{attr[1]}`")
                        else:
                            sections.append(f"- `{attr}`")
                    sections.append("")
                
                # Add abilities for walkers
                abilities = entity.get("abilities", [])
                if abilities:
                    sections.append("**Abilities:**\n")
                    for ability in abilities:
                        sections.append(f"- `{ability}`")
                    sections.append("")
                
                docstring = entity.get("docstring", "")
                if docstring:
                    sections.append(f"{docstring}\n")
        
        sections.append("---\n")
    
    return "\n".join(sections)

def generate_overview_with_llm(repo_name: str, readme_summary: str, entities: List[Dict[str, Any]]) -> str:
    """
    Generate a natural language overview using LLM
    
    Args:
        repo_name: Name of the repository
        readme_summary: Summary of the README file
        entities: List of code entities
        
    Returns:
        AI-generated project overview
    """
    # Prepare context
    entity_summary = {
        "classes": len([e for e in entities if e["type"] == "class"]),
        "functions": len([e for e in entities if e["type"] == "function"]),
        "walkers": len([e for e in entities if e["type"] == "walker"]),
        "nodes": len([e for e in entities if e["type"] == "node"]),
        "total": len(entities)
    }
    
    # Get sample entities
    sample_classes = [e["name"] for e in entities if e["type"] == "class"][:5]
    sample_functions = [e["name"] for e in entities if e["type"] == "function"][:5]
    sample_walkers = [e["name"] for e in entities if e["type"] == "walker"][:5]
    
    prompt = f"""You are a technical documentation writer. Generate a clear and concise project overview (2-3 paragraphs) for a repository called "{repo_name}".

README Summary:
{readme_summary}

Code Statistics:
- Total Entities: {entity_summary['total']}
- Classes: {entity_summary['classes']}
- Functions: {entity_summary['functions']}
- Walkers (Jac agents): {entity_summary['walkers']}
- Nodes (Jac data structures): {entity_summary['nodes']}

Sample Classes: {', '.join(sample_classes) if sample_classes else 'None'}
Sample Functions: {', '.join(sample_functions) if sample_functions else 'None'}
Sample Walkers: {', '.join(sample_walkers) if sample_walkers else 'None'}

Write a professional overview that explains:
1. What this project does and its main purpose
2. Its architectural structure and key design patterns
3. The main components and their roles in the system

Use clear, technical language. Be specific but concise. Focus on the big picture."""

    try:
        overview = llm_helper.call_llm(prompt, max_tokens=500)
        return overview.strip()
    except Exception as e:
        print(f"Error generating overview: {e}")
        # Fallback to template-based overview
        return generate_template_overview(repo_name, readme_summary, entity_summary, sample_classes, sample_functions)

def generate_template_overview(repo_name: str, readme_summary: str, 
                               entity_summary: Dict[str, int],
                               sample_classes: List[str],
                               sample_functions: List[str]) -> str:
    """
    Generate a template-based overview (fallback when LLM fails)
    
    Args:
        repo_name: Repository name
        readme_summary: README summary
        entity_summary: Statistics about entities
        sample_classes: Sample class names
        sample_functions: Sample function names
        
    Returns:
        Template-based overview
    """
    overview = f"""**{repo_name}** is a software project that {readme_summary[:200]}

The codebase contains {entity_summary['total']} analyzed components, including {entity_summary['classes']} classes and {entity_summary['functions']} functions. """
    
    if entity_summary['walkers'] > 0:
        overview += f"This project uses the Jac programming language with {entity_summary['walkers']} walkers (agents) and {entity_summary['nodes']} nodes (data structures), indicating a graph-based or agent-oriented architecture. "
    
    if sample_classes:
        overview += f"\n\nKey classes include: {', '.join(sample_classes[:3])}. "
    
    if sample_functions:
        overview += f"Main functions include: {', '.join(sample_functions[:3])}."
    
    return overview

def generate_installation_section(repo_name: str, local_path: str) -> str:
    """
    Generate installation instructions based on detected project files
    
    Args:
        repo_name: Repository name
        local_path: Local path to repository
        
    Returns:
        Markdown formatted installation section
    """
    section = "## 📦 Installation\n\n"
    
    # Check for common dependency files
    has_requirements = os.path.exists(os.path.join(local_path, "requirements.txt"))
    has_pyproject = os.path.exists(os.path.join(local_path, "pyproject.toml"))
    has_setup_py = os.path.exists(os.path.join(local_path, "setup.py"))
    has_package_json = os.path.exists(os.path.join(local_path, "package.json"))
    has_cargo_toml = os.path.exists(os.path.join(local_path, "Cargo.toml"))
    has_go_mod = os.path.exists(os.path.join(local_path, "go.mod"))
    has_gemfile = os.path.exists(os.path.join(local_path, "Gemfile"))
    
    if has_requirements or has_pyproject or has_setup_py:
        section += "### Python Project Setup\n\n"
        section += "```bash\n"
        section += "# Clone the repository\n"
        section += f"git clone <repository-url>\n"
        section += f"cd {repo_name}\n\n"
        section += "# Create and activate virtual environment\n"
        section += "python3 -m venv venv\n"
        section += "source venv/bin/activate  # On Windows: venv\\Scripts\\activate\n\n"
        
        if has_requirements:
            section += "# Install dependencies\n"
            section += "pip install -r requirements.txt\n"
        elif has_setup_py:
            section += "# Install package\n"
            section += "pip install -e .\n"
        elif has_pyproject:
            section += "# Install dependencies (using poetry or pip)\n"
            section += "pip install -e .  # or: poetry install\n"
        
        section += "```\n\n"
    
    elif has_package_json:
        section += "### Node.js Project Setup\n\n"
        section += "```bash\n"
        section += "# Clone the repository\n"
        section += f"git clone <repository-url>\n"
        section += f"cd {repo_name}\n\n"
        section += "# Install dependencies\n"
        section += "npm install\n"
        section += "# or using yarn:\n"
        section += "# yarn install\n"
        section += "```\n\n"
    
    elif has_cargo_toml:
        section += "### Rust Project Setup\n\n"
        section += "```bash\n"
        section += "# Clone the repository\n"
        section += f"git clone <repository-url>\n"
        section += f"cd {repo_name}\n\n"
        section += "# Build the project\n"
        section += "cargo build --release\n"
        section += "```\n\n"
    
    elif has_go_mod:
        section += "### Go Project Setup\n\n"
        section += "```bash\n"
        section += "# Clone the repository\n"
        section += f"git clone <repository-url>\n"
        section += f"cd {repo_name}\n\n"
        section += "# Download dependencies\n"
        section += "go mod download\n\n"
        section += "# Build the project\n"
        section += "go build\n"
        section += "```\n\n"
    
    elif has_gemfile:
        section += "### Ruby Project Setup\n\n"
        section += "```bash\n"
        section += "# Clone the repository\n"
        section += f"git clone <repository-url>\n"
        section += f"cd {repo_name}\n\n"
        section += "# Install dependencies\n"
        section += "bundle install\n"
        section += "```\n\n"
    
    else:
        section += "### Basic Setup\n\n"
        section += "```bash\n"
        section += "# Clone the repository\n"
        section += f"git clone <repository-url>\n"
        section += f"cd {repo_name}\n"
        section += "```\n\n"
        section += "*Note: Specific installation instructions not automatically detected. Please refer to the repository's README for detailed setup instructions.*\n\n"
    
    return section

def generate_usage_section(entities: List[Dict[str, Any]]) -> str:
    """
    Generate usage examples section
    
    Args:
        entities: List of code entities
        
    Returns:
        Markdown formatted usage section
    """
    section = "## 🚀 Usage\n\n"
    
    # Look for main entry points
    main_functions = []
    for entity in entities:
        if entity["type"] == "function":
            name = entity["name"].lower()
            if name in ["main", "run", "execute", "start"]:
                main_functions.append(entity)
    
    if main_functions:
        section += "### Main Entry Points\n\n"
        for func in main_functions[:3]:
            section += f"**`{func['name']}()`**\n\n"
            if func.get("docstring"):
                section += f"{func['docstring'][:200]}\n\n"
    else:
        section += "*Usage examples will depend on your specific implementation. Refer to the API Reference below for detailed function documentation.*\n\n"
    
    # Check for CLI usage
    has_cli = any(
        entity["type"] == "function" and 
        any(keyword in entity["name"].lower() for keyword in ["cli", "parse", "argparse"])
        for entity in entities
    )
    
    if has_cli:
        section += "### Command Line Interface\n\n"
        section += "```bash\n"
        section += "# Run the application\n"
        section += "python main.py --help\n"
        section += "```\n\n"
    
    return section

def generate_statistics_section(entities: List[Dict[str, Any]]) -> str:
    """
    Generate code statistics section
    
    Args:
        entities: List of code entities
        
    Returns:
        Markdown formatted statistics
    """
    stats = {
        "total_files": len(set(e["file_path"] for e in entities)),
        "total_classes": len([e for e in entities if e["type"] == "class"]),
        "total_functions": len([e for e in entities if e["type"] == "function"]),
        "total_walkers": len([e for e in entities if e["type"] == "walker"]),
        "total_nodes": len([e for e in entities if e["type"] == "node"]),
        "total_edges": len([e for e in entities if e["type"] == "edge"]),
        "total_lines": sum(e.get("line_end", 0) - e.get("line_start", 0) for e in entities)
    }
    
    section = "## 📊 Code Statistics\n\n"
    section += f"- **Total Files Analyzed:** {stats['total_files']}\n"
    section += f"- **Total Code Entities:** {len(entities)}\n"
    section += f"- **Classes:** {stats['total_classes']}\n"
    section += f"- **Functions:** {stats['total_functions']}\n"
    
    if stats['total_walkers'] > 0:
        section += f"- **Walkers (Jac):** {stats['total_walkers']}\n"
    if stats['total_nodes'] > 0:
        section += f"- **Nodes (Jac):** {stats['total_nodes']}\n"
    if stats['total_edges'] > 0:
        section += f"- **Edges (Jac):** {stats['total_edges']}\n"
    
    section += f"- **Approximate Lines of Code:** {stats['total_lines']}\n\n"
    
    # Add complexity analysis
    complexities = [e.get("complexity", 0) for e in entities if e.get("complexity", 0) > 0]
    if complexities:
        avg_complexity = sum(complexities) / len(complexities)
        max_complexity = max(complexities)
        section += f"- **Average Function Complexity:** {avg_complexity:.2f}\n"
        section += f"- **Maximum Function Complexity:** {max_complexity}\n\n"
    
    return section

def generate_documentation(doc_data: Dict[str, Any], output_dir: str) -> str:
    """
    Main function to generate complete documentation
    
    Args:
        doc_data: Dictionary containing all documentation data
        output_dir: Directory to save documentation
        
    Returns:
        Path to generated documentation file
    """
    repo_name = doc_data["repo_name"]
    entities = doc_data["code_entities"]
    local_path = doc_data["local_path"]
    
    # Create output directory
    output_path = Path(output_dir) / repo_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    doc_file = output_path / "docs.md"
    
    # Start building documentation
    doc_lines = []
    
    # Header with banner
    doc_lines.append(f"# 📚 {repo_name}\n")
    doc_lines.append(f"> **Comprehensive Code Documentation**\n")
    doc_lines.append(f"> *Auto-generated by Codebase Genius on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}*\n")
    doc_lines.append("---\n")
    
    # Table of Contents
    doc_lines.append("## 📑 Table of Contents\n")
    doc_lines.append("1. [Overview](#-overview)")
    doc_lines.append("2. [Installation](#-installation)")
    doc_lines.append("3. [Usage](#-usage)")
    doc_lines.append("4. [Repository Structure](#-repository-structure)")
    doc_lines.append("5. [Architecture](#-architecture)")
    doc_lines.append("6. [Code Statistics](#-code-statistics)")
    doc_lines.append("7. [API Reference](#-api-reference)")
    doc_lines.append("\n---\n")
    
    # Overview
    doc_lines.append("## 🎯 Overview\n")
    overview = generate_overview_with_llm(
        repo_name, 
        doc_data["readme_summary"], 
        entities
    )
    doc_lines.append(overview)
    doc_lines.append("\n")
    
    # Installation
    doc_lines.append(generate_installation_section(repo_name, local_path))
    
    # Usage
    doc_lines.append(generate_usage_section(entities))
    
    # Repository Structure
    doc_lines.append("## 📂 Repository Structure\n\n")
    file_tree_md = generate_file_tree_markdown(doc_data["file_tree"])
    doc_lines.append(file_tree_md)
    doc_lines.append("\n")
    
    # Architecture Diagrams
    doc_lines.append("## 🏗️ Architecture\n\n")
    
    if entities:
        # Class diagram
        doc_lines.append("### Class Diagram\n\n")
        class_diagram = generate_mermaid_class_diagram(entities)
        doc_lines.append(class_diagram)
        doc_lines.append("\n")
        
        # Flow diagram for Jac projects
        if any(e["type"] == "walker" for e in entities):
            doc_lines.append("### Workflow Diagram\n\n")
            flow_diagram = generate_mermaid_flow_diagram(entities)
            doc_lines.append(flow_diagram)
            doc_lines.append("\n")
    else:
        doc_lines.append("*No architecture diagram available - no code entities found*\n\n")
    
    # Statistics
    doc_lines.append(generate_statistics_section(entities))
    
    # API Reference
    doc_lines.append("## 📚 API Reference\n\n")
    
    if entities:
        api_ref = generate_api_reference(entities)
        doc_lines.append(api_ref)
    else:
        doc_lines.append("*No API reference available - no code entities were analyzed*\n\n")
    
    # Contributing Section
    doc_lines.append("## 🤝 Contributing\n\n")
    doc_lines.append("Contributions are welcome! Please feel free to submit a Pull Request.\n\n")
    
    # License Section
    doc_lines.append("## 📄 License\n\n")
    doc_lines.append("Please refer to the LICENSE file in the repository.\n\n")
    
    # Footer
    doc_lines.append("---\n\n")
    doc_lines.append("**📝 Documentation Notes:**\n")
    doc_lines.append(f"- Generated from: `{doc_data['repo_url']}`\n")
    doc_lines.append(f"- Total entities documented: {len(entities)}\n")
    doc_lines.append(f"- Documentation format: Markdown with Mermaid diagrams\n\n")
    doc_lines.append("*This documentation was automatically generated by **Codebase Genius** - An AI-powered multi-agent documentation system*\n")
    doc_lines.append("\n🔗 [Codebase Genius](https://github.com/your-repo/codebase-genius)\n")
    
    # Write to file
    final_content = "\n".join(doc_lines)
    
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"✅ Documentation written to: {doc_file}")
    print(f"📄 File size: {format_size(len(final_content.encode('utf-8')))}")
    print(f"📊 Sections generated: 8")
    print(f"🎨 Diagrams included: {2 if any(e['type'] == 'walker' for e in entities) else 1}")
    
    return str(doc_file)

def generate_quick_reference(entities: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a quick reference card (optional bonus output)
    
    Args:
        entities: List of code entities
        output_path: Path to save quick reference
    """
    lines = ["# Quick Reference\n"]
    
    # Most important classes
    classes = [e for e in entities if e["type"] == "class"][:5]
    if classes:
        lines.append("## Key Classes\n")
        for cls in classes:
            lines.append(f"- **{cls['name']}**: {cls.get('docstring', 'No description')[:80]}")
        lines.append("")
    
    # Most important functions
    functions = [e for e in entities if e["type"] == "function"][:5]
    if functions:
        lines.append("## Key Functions\n")
        for func in functions:
            lines.append(f"- **{func['name']}()**: {func.get('docstring', 'No description')[:80]}")
        lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))