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
from langchain_core.documents import Document

TREE_SITTER_LANGUAGES = {
    "python": tree_sitter_python.language,
    "java": tree_sitter_java.language,
    "javascript": tree_sitter_javascript.language,
    "typescript": tree_sitter_typescript.language_tsx,
    "html": tree_sitter_html.language,
    "css": tree_sitter_css.language,
    "c": tree_sitter_c.language,
    "cpp": tree_sitter_cpp.language,
    "csharp": tree_sitter_c_sharp.language,
    "go": tree_sitter_go.language,
    "rust": tree_sitter_rust.language,
    "php": tree_sitter_php.language_php,
    "ruby": tree_sitter_ruby.language,
}


class CodeParser:

    def __init__(self):
        self.languages = {}

        for name, language in TREE_SITTER_LANGUAGES.items():
            self.languages[name] = Language(language())

    def parse(self, code, language,file_name,file_path):
        if language in ["markdown","text","json","csv"]:
            document = Document(
                page_content=code,
                metadata={
                    "language": language,
                    "file_name": file_name,
                    "file_path": file_path
                }
            )

            return document
            
        else:
            parser = Parser(self.languages[language])

            tree = parser.parse(code.encode("utf-8"))

            return tree,language,code,file_name,file_path
        

    

