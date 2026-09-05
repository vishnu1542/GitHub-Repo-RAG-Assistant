from tree_sitter import Language, Parser
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


class CodeParser:

    def __init__(self):
        self.languages = {}

        for name, language in TREE_SITTER_LANGUAGES.items():
            self.languages[name] = Language(language.language())

    def parse(self, code, language,file_name,file_path):

        parser = Parser(self.languages[language])

        tree = parser.parse(code.encode("utf-8"))

        return tree,language,code,file_name,file_path

    

