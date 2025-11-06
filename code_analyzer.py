"""
Code Analyzer Module
Parses source code and builds Code Context Graph (CCG)

This module provides comprehensive code analysis capabilities:
- Python file parsing using AST
- Jac file parsing using regex
- Code Context Graph (CCG) construction
- Relationship mapping (calls, inheritance, imports)
- Code complexity metrics
"""

import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class CodeEntity:
    """Represents a code entity (function, class, method, etc.)"""
    def __init__(self, name, entity_type, file_path, line_start, line_end,
                 docstring="", parameters=None, dependencies=None, **kwargs):
        self.name = name
        self.type = entity_type
        self.file_path = file_path
        self.line_start = line_start
        self.line_end = line_end
        self.docstring = docstring
        self.parameters = parameters or []
        self.dependencies = dependencies or []
        self.extra = kwargs

def parse_python_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse Python file and extract functions, classes, and their relationships
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of dictionaries containing entity information
    """
    entities = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file into an AST
        tree = ast.parse(content, filename=file_path)
        
        # Extract module-level imports
        module_imports = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_imports.append({
                        'name': alias.name,
                        'asname': alias.asname,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        module_imports.append({
                            'module': node.module,
                            'name': alias.name,
                            'asname': alias.asname,
                            'line': node.lineno
                        })
        
        # Extract functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get docstring
                docstring = ast.get_docstring(node) or ""
                
                # Get parameters
                params = []
                for arg in node.args.args:
                    param_info = {
                        'name': arg.arg,
                        'annotation': ast.unparse(arg.annotation) if arg.annotation else None
                    }
                    params.append(param_info)
                
                # Get return type annotation
                return_type = ast.unparse(node.returns) if node.returns else None
                
                # Get decorators
                decorators = [ast.unparse(dec) for dec in node.decorator_list]
                
                # Get function calls (dependencies)
                calls = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            calls.append(child.func.attr)
                
                # Get variables assigned in function
                variables = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                variables.append(target.id)
                
                entities.append({
                    "name": node.name,
                    "type": "function",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": docstring,
                    "parameters": params,
                    "return_type": return_type,
                    "decorators": decorators,
                    "dependencies": list(set(calls)),
                    "variables": list(set(variables)),
                    "imports": module_imports,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "complexity": calculate_function_complexity(node)
                })
            
            elif isinstance(node, ast.ClassDef):
                # Get docstring
                docstring = ast.get_docstring(node) or ""
                
                # Get base classes
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(ast.unparse(base))
                
                # Get decorators
                decorators = [ast.unparse(dec) for dec in node.decorator_list]
                
                # Get methods
                methods = []
                class_attributes = []
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'is_static': any(
                                isinstance(d, ast.Name) and d.id == 'staticmethod' 
                                for d in item.decorator_list
                            ),
                            'is_class': any(
                                isinstance(d, ast.Name) and d.id == 'classmethod' 
                                for d in item.decorator_list
                            ),
                            'is_property': any(
                                isinstance(d, ast.Name) and d.id == 'property' 
                                for d in item.decorator_list
                            )
                        }
                        methods.append(method_info)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_attributes.append(target.id)
                
                entities.append({
                    "name": node.name,
                    "type": "class",
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": docstring,
                    "parameters": bases,  # Base classes
                    "decorators": decorators,
                    "dependencies": [m['name'] for m in methods],
                    "bases": bases,
                    "methods": methods,
                    "attributes": class_attributes,
                    "imports": module_imports,
                    "method_count": len(methods)
                })
    
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return entities

def calculate_function_complexity(node: ast.FunctionDef) -> int:
    """
    Calculate cyclomatic complexity of a function
    
    Args:
        node: AST node of the function
        
    Returns:
        Integer representing complexity
    """
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        # Count decision points
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    
    return complexity

def parse_jac_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse Jac file using regex-based parsing
    
    Args:
        file_path: Path to the Jac file
        
    Returns:
        List of dictionaries containing entity information
    """
    entities = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find walkers with their full definitions
        walker_pattern = r'walker\s+(\w+)\s*{([^}]*)}'
        for match in re.finditer(walker_pattern, content, re.DOTALL):
            walker_name = match.group(1)
            walker_body = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            end_line = content[:match.end()].count('\n') + 1
            
            # Extract 'has' attributes
            has_pattern = r'has\s+(\w+)\s*:\s*(\w+)'
            attributes = re.findall(has_pattern, walker_body)
            
            # Extract 'can' abilities
            can_pattern = r'can\s+(\w+)'
            abilities = re.findall(can_pattern, walker_body)
            
            entities.append({
                "name": walker_name,
                "type": "walker",
                "line_start": start_line,
                "line_end": end_line,
                "docstring": extract_jac_docstring(walker_body),
                "parameters": attributes,
                "dependencies": abilities,
                "attributes": attributes,
                "abilities": abilities
            })
        
        # Find nodes
        node_pattern = r'node\s+(\w+)\s*{([^}]*)}'
        for match in re.finditer(node_pattern, content, re.DOTALL):
            node_name = match.group(1)
            node_body = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            end_line = content[:match.end()].count('\n') + 1
            
            # Extract 'has' attributes
            has_pattern = r'has\s+(\w+)\s*:\s*(\w+)'
            attributes = re.findall(has_pattern, node_body)
            
            entities.append({
                "name": node_name,
                "type": "node",
                "line_start": start_line,
                "line_end": end_line,
                "docstring": extract_jac_docstring(node_body),
                "parameters": attributes,
                "dependencies": [],
                "attributes": attributes
            })
        
        # Find edges
        edge_pattern = r'edge\s+(\w+)'
        for match in re.finditer(edge_pattern, content):
            edge_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            
            entities.append({
                "name": edge_name,
                "type": "edge",
                "line_start": start_line,
                "line_end": start_line,
                "docstring": "",
                "parameters": [],
                "dependencies": []
            })
        
        # Find standalone abilities
        ability_pattern = r'can\s+(\w+)\s+with'
        for match in re.finditer(ability_pattern, content):
            ability_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            
            entities.append({
                "name": ability_name,
                "type": "ability",
                "line_start": start_line,
                "line_end": start_line + 5,
                "docstring": "",
                "parameters": [],
                "dependencies": []
            })
    
    except Exception as e:
        print(f"Error parsing Jac file {file_path}: {e}")
    
    return entities

def extract_jac_docstring(body: str) -> str:
    """
    Extract docstring from Jac code body
    
    Args:
        body: String containing Jac code
        
    Returns:
        Extracted docstring or empty string
    """
    # Look for triple-quoted strings at the beginning
    docstring_pattern = r'^\s*"""(.*?)"""'
    match = re.search(docstring_pattern, body, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ""

def parse_file(repo_path: str, file_rel_path: str, language: str) -> List[Dict[str, Any]]:
    """
    Parse a file based on its language
    
    Args:
        repo_path: Root path of the repository
        file_rel_path: Relative path to the file
        language: Programming language of the file
        
    Returns:
        List of extracted entities
    """
    full_path = os.path.join(repo_path, file_rel_path)
    
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return []
    
    try:
        if language == "python":
            return parse_python_file(full_path)
        elif language == "jac":
            return parse_jac_file(full_path)
        else:
            print(f"Unsupported language: {language}")
            return []
    except Exception as e:
        print(f"Error parsing file {full_path}: {e}")
        return []

def build_ccg(repo_path: str, entities: List[Any]) -> Dict[str, Any]:
    """
    Build Code Context Graph from entities
    
    Args:
        repo_path: Root path of the repository
        entities: List of code entities
        
    Returns:
        Dictionary representing the CCG with nodes and edges
    """
    ccg = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "total_nodes": 0,
            "total_edges": 0,
            "languages": set()
        }
    }
    
    # Create nodes and build entity lookup
    entity_dict = {}
    
    for entity in entities:
        node_id = f"{entity.file_path}::{entity.name}"
        entity_dict[entity.name] = {
            'id': node_id,
            'entity': entity
        }
        
        ccg["nodes"].append({
            "id": node_id,
            "name": entity.name,
            "type": entity.type,
            "file": entity.file_path,
            "line": entity.line_start,
            "docstring": entity.docstring[:100] if entity.docstring else "",
            "parameters": entity.parameters
        })
    
    # Create edges (relationships)
    for entity in entities:
        source_id = f"{entity.file_path}::{entity.name}"
        
        # Function calls
        for dep in entity.dependencies:
            if dep in entity_dict:
                target_id = entity_dict[dep]['id']
                ccg["edges"].append({
                    "source": source_id,
                    "target": target_id,
                    "type": "calls",
                    "label": "calls"
                })
        
        # Inheritance (for classes)
        if entity.type == "class" and hasattr(entity, 'parameters'):
            for base in entity.parameters:
                if base in entity_dict:
                    target_id = entity_dict[base]['id']
                    ccg["edges"].append({
                        "source": source_id,
                        "target": target_id,
                        "type": "inherits",
                        "label": "inherits from"
                    })
    
    # Update metadata
    ccg["metadata"]["total_nodes"] = len(ccg["nodes"])
    ccg["metadata"]["total_edges"] = len(ccg["edges"])
    
    return ccg

def analyze_complexity(entities: List[Any]) -> Dict[str, Any]:
    """
    Analyze code complexity metrics
    
    Args:
        entities: List of code entities
        
    Returns:
        Dictionary containing complexity statistics
    """
    stats = {
        "total_functions": 0,
        "total_classes": 0,
        "total_walkers": 0,
        "total_nodes": 0,
        "avg_function_length": 0,
        "max_function_length": 0,
        "avg_complexity": 0,
        "max_complexity": 0,
        "total_methods": 0,
        "files_analyzed": set()
    }
    
    function_lengths = []
    complexities = []
    
    for entity in entities:
        stats["files_analyzed"].add(entity.file_path)
        
        if entity.type == "function":
            stats["total_functions"] += 1
            length = entity.line_end - entity.line_start
            function_lengths.append(length)
            stats["max_function_length"] = max(stats["max_function_length"], length)
            
            if hasattr(entity, 'complexity'):
                complexities.append(entity.complexity)
                stats["max_complexity"] = max(stats["max_complexity"], entity.complexity)
        
        elif entity.type == "class":
            stats["total_classes"] += 1
            if hasattr(entity, 'methods'):
                stats["total_methods"] += len(entity.methods)
        
        elif entity.type == "walker":
            stats["total_walkers"] += 1
        
        elif entity.type == "node":
            stats["total_nodes"] += 1
    
    # Calculate averages
    if function_lengths:
        stats["avg_function_length"] = sum(function_lengths) / len(function_lengths)
    
    if complexities:
        stats["avg_complexity"] = sum(complexities) / len(complexities)
    
    stats["files_analyzed"] = len(stats["files_analyzed"])
    
    return stats

def find_related_entities(entity_name: str, entities: List[Any], relationship_type: str = "all") -> List[Dict[str, Any]]:
    """
    Find entities related to a given entity
    
    Args:
        entity_name: Name of the entity to search for
        entities: List of all entities
        relationship_type: Type of relationship ('calls', 'called_by', 'inherits', 'all')
        
    Returns:
        List of related entities
    """
    related = []
    
    # Find the target entity
    target = None
    for entity in entities:
        if entity.name == entity_name:
            target = entity
            break
    
    if not target:
        return []
    
    # Find related entities based on relationship type
    if relationship_type in ["calls", "all"]:
        # Find what this entity calls
        for dep in target.dependencies:
            for entity in entities:
                if entity.name == dep:
                    related.append({
                        "entity": entity.name,
                        "type": entity.type,
                        "relationship": "calls",
                        "file": entity.file_path
                    })
    
    if relationship_type in ["called_by", "all"]:
        # Find what calls this entity
        for entity in entities:
            if target.name in entity.dependencies:
                related.append({
                    "entity": entity.name,
                    "type": entity.type,
                    "relationship": "called_by",
                    "file": entity.file_path
                })
    
    if relationship_type in ["inherits", "all"] and target.type == "class":
        # Find inheritance relationships
        for base in target.parameters:
            for entity in entities:
                if entity.name == base:
                    related.append({
                        "entity": entity.name,
                        "type": entity.type,
                        "relationship": "inherits_from",
                        "file": entity.file_path
                    })
    
    return related