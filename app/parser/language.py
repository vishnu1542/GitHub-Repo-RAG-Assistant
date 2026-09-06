from typing import Any,List,Dict
import tree_sitter_python
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_html
import tree_sitter_css
import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_c_sharp
import tree_sitter_go
import tree_sitter_rust
import tree_sitter_php
import tree_sitter_ruby
ALLOWED_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".cpp",
    ".c",
    ".h",
    ".go",
    ".csv",
    ".txt",
    ".json",
    ".md"
}
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build"
}
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".html": "html",
    ".htm": "html",
    ".csv":"csv",
    ".json":"json",
    ".txt":"text",
    ".md":"markdown",
    ".css": "css",
    ".scss": "scss",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
}
TREE_SITTER_LANGUAGES = {
    "python": tree_sitter_python,
    "java": tree_sitter_java,
    "javascript": tree_sitter_javascript,
    "typescript": tree_sitter_typescript,
    "html": tree_sitter_html,
    "css": tree_sitter_css,
    "c": tree_sitter_c,
    "cpp": tree_sitter_cpp,
    "csharp": tree_sitter_c_sharp,
    "go": tree_sitter_go,
    "rust": tree_sitter_rust,
    "php": tree_sitter_php,
    "ruby": tree_sitter_ruby,
}
CHUNK_NODE_TYPES = {

    "python": {
        "class": "class_definition",
        "method": "function_definition",
        "function": "function_definition"
    },

    "java": {
        "class": "class_declaration",
        "method": "method_declaration",
        "function": None
    },

    "javascript": {
        "class": "class_declaration",
        "method": "method_definition",
        "function": "function_declaration"
    },

    "typescript": {
        "class": "class_declaration",
        "method": "method_definition",
        "function": "function_declaration"
    },

    "tsx": {
        "class": "class_declaration",
        "method": "method_definition",
        "function": "function_declaration"
    },

    "c": {
        "class": None,
        "method": "function_definition",
        "function": "function_definition"
    },

    "cpp": {
        "class": "class_specifier",
        "method": "function_definition",
        "function": "function_definition"
    },

    "csharp": {
        "class": "class_declaration",
        "method": "method_declaration",
        "function": None
    },

    "go": {
        "class": None,
        "method": "method_declaration",
        "function": "function_declaration"
    },

    "rust": {
        "class": "struct_item",
        "method": "function_item",
        "function": "function_item"
    },

    "php": {
        "class": "class_declaration",
        "method": "method_declaration",
        "function": "function_definition"
    },

    "ruby": {
        "class": "class",
        "method": "method",
        "function": "method"
    }
}