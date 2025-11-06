"""
Codebase Genius - Multi-Agent Code Documentation System
Main Jac Implementation
"""

import:py from dotenv { load_dotenv }
import:py os;
import:py json;
import:py from datetime { datetime }

# Import our Python helper modules
import:py repo_mapper;
import:py code_analyzer;
import:py doc_generator;
import:py llm_helper;

# Load environment variables
glob ENV_LOADED = load_dotenv();

# Node definitions for our graph structure
node Repository {
    has url: str;
    has name: str;
    has local_path: str;
    has file_tree: dict;
    has readme_summary: str;
    has status: str = "initialized";
}

node FileNode {
    has path: str;
    has type: str;  # 'file' or 'directory'
    has language: str;
    has analyzed: bool = False;
}

node CodeEntity {
    has name: str;
    has type: str;  # 'function', 'class', 'method'
    has file_path: str;
    has line_start: int;
    has line_end: int;
    has docstring: str;
    has parameters: list;
    has dependencies: list;
}

node Documentation {
    has repo_name: str;
    has content: str;
    has diagrams: list;
    has generated_at: str;
    has status: str = "pending";
}

# Edge definitions for relationships
edge contains;
edge calls;
edge inherits;
edge imports;
edge documents;

# Walker: Code Genius Supervisor
walker CodeGenius {
    has github_url: str;
    has output_dir: str = "./outputs";
    has status: str = "starting";
    has results: dict = {};
    
    can process_repository with `root entry {
        # Step 1: Initialize
        print(f"[CodeGenius] Starting documentation for: {self.github_url}");
        self.status = "mapping_repository";
        
        # Create repository node
        repo_node = here ++> Repository(
            url=self.github_url,
            name="",
            local_path="",
            file_tree={},
            readme_summary=""
        );
        
        # Step 2: Trigger RepoMapper
        visit repo_node with RepoMapper(url=self.github_url);
        
        # Step 3: Trigger CodeAnalyzer
        if repo_node.status == "mapped":
            self.status = "analyzing_code";
            visit repo_node with CodeAnalyzer();
        
        # Step 4: Trigger DocGenie
        if repo_node.status == "analyzed":
            self.status = "generating_docs";
            visit repo_node with DocGenie(output_dir=self.output_dir);
        
        # Step 5: Collect results
        self.results = {
            "status": "completed",
            "repository": repo_node.name,
            "output_path": f"{self.output_dir}/{repo_node.name}/docs.md",
            "timestamp": datetime.now().isoformat()
        };
        
        print(f"[CodeGenius] Documentation completed: {self.results['output_path']}");
        report self.results;
    }
}

# Walker: Repository Mapper
walker RepoMapper {
    has url: str;
    
    can map_repository with Repository entry {
        print(f"[RepoMapper] Mapping repository: {self.url}");
        
        try {
            # Clone and analyze repository
            repo_data = repo_mapper.clone_and_map(self.url);
            
            # Update repository node
            here.name = repo_data["name"];
            here.local_path = repo_data["local_path"];
            here.file_tree = repo_data["file_tree"];
            here.readme_summary = repo_data["readme_summary"];
            here.status = "mapped";
            
            # Create file nodes
            files_to_analyze = repo_data.get("important_files", []);
            for file_info in files_to_analyze {
                file_node = here ++> FileNode(
                    path=file_info["path"],
                    type="file",
                    language=file_info.get("language", "unknown")
                ) :contains:;
            }
            
            print(f"[RepoMapper] Mapped {len(files_to_analyze)} files");
            
        } except Exception as e {
            print(f"[RepoMapper] Error: {str(e)}");
            here.status = "error";
            report {"error": str(e)};
        }
    }
}

# Walker: Code Analyzer
walker CodeAnalyzer {
    has ccg: dict = {};  # Code Context Graph
    
    can analyze_code with Repository entry {
        print(f"[CodeAnalyzer] Analyzing code structure...");
        
        try {
            # Get all file nodes
            file_nodes = [node for node in -->(:FileNode:)];
            
            # Analyze each file
            for file_node in file_nodes {
                if file_node.language in ["python", "jac"]:
                    entities = code_analyzer.parse_file(
                        here.local_path, 
                        file_node.path,
                        file_node.language
                    );
                    
                    # Create code entity nodes
                    for entity in entities {
                        entity_node = here ++> CodeEntity(
                            name=entity["name"],
                            type=entity["type"],
                            file_path=file_node.path,
                            line_start=entity.get("line_start", 0),
                            line_end=entity.get("line_end", 0),
                            docstring=entity.get("docstring", ""),
                            parameters=entity.get("parameters", []),
                            dependencies=entity.get("dependencies", [])
                        );
                    }
                    
                    file_node.analyzed = True;
                }
            }
            
            # Build relationship graph
            self.ccg = code_analyzer.build_ccg(here.local_path, [
                node for node in -->(:CodeEntity:)
            ]);
            
            here.status = "analyzed";
            print(f"[CodeAnalyzer] Analysis complete. Found {len(-->(:CodeEntity:))} entities");
            
        } except Exception as e {
            print(f"[CodeAnalyzer] Error: {str(e)}");
            here.status = "error";
        }
    }
}

# Walker: Documentation Generator
walker DocGenie {
    has output_dir: str;
    
    can generate_docs with Repository entry {
        print(f"[DocGenie] Generating documentation...");
        
        try {
            # Collect all data
            code_entities = [node for node in -->(:CodeEntity:)];
            
            doc_data = {
                "repo_name": here.name,
                "repo_url": here.url,
                "readme_summary": here.readme_summary,
                "file_tree": here.file_tree,
                "code_entities": [
                    {
                        "name": e.name,
                        "type": e.type,
                        "file_path": e.file_path,
                        "docstring": e.docstring,
                        "parameters": e.parameters,
                        "line_start": e.line_start,
                        "line_end": e.line_end
                    } for e in code_entities
                ],
                "local_path": here.local_path
            };
            
            # Generate markdown documentation
            output_path = doc_generator.generate_documentation(
                doc_data,
                self.output_dir
            );
            
            # Create documentation node
            doc_node = here ++> Documentation(
                repo_name=here.name,
                content="Generated",
                diagrams=[],
                generated_at=datetime.now().isoformat(),
                status="completed"
            ) :documents:;
            
            here.status = "documented";
            print(f"[DocGenie] Documentation saved to: {output_path}");
            
        } except Exception as e {
            print(f"[DocGenie] Error: {str(e)}");
            here.status = "error";
        }
    }
}

# Walker: API Handler for HTTP requests
walker DocumentRepository {
    has github_url: str;
    has output_dir: str = "./outputs";
    
    can handle_request with `root entry {
        # Validate URL
        if not self.github_url or not self.github_url.startswith("http"):
            report {
                "status": "error",
                "message": "Invalid GitHub URL provided"
            };
            disengage;
        }
        
        # Start the documentation process
        result = spawn here walker CodeGenius(
            github_url=self.github_url,
            output_dir=self.output_dir
        );
        
        report result;
    }
}

# Walker: Query the Code Context Graph
walker QueryCCG {
    has query_type: str;  # 'callers', 'callees', 'imports', 'structure'
    has entity_name: str;
    
    can query with Repository entry {
        entities = [node for node in -->(:CodeEntity:)];
        
        if self.query_type == "structure":
            # Return overall structure
            structure = {};
            for entity in entities {
                file = entity.file_path;
                if file not in structure:
                    structure[file] = [];
                structure[file].append({
                    "name": entity.name,
                    "type": entity.type
                });
            }
            report {"structure": structure};
        
        elif self.query_type == "find":
            # Find specific entity
            matches = [
                {
                    "name": e.name,
                    "type": e.type,
                    "file": e.file_path,
                    "line": e.line_start,
                    "docstring": e.docstring
                }
                for e in entities if self.entity_name.lower() in e.name.lower()
            ];
            report {"matches": matches};
        
        else:
            report {"error": "Unknown query type"};
    }
}