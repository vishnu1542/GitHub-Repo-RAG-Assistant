from parser.language import CHUNK_NODE_TYPES
class CodeChunk:
    def get_chunks(self,root,code,language,file_name,file_path):
        chunks=[]
        self.Class=CHUNK_NODE_TYPES[language]["class"]
        self.method=CHUNK_NODE_TYPES[language]["method"]
        self.function=CHUNK_NODE_TYPES[language]["function"]
        
        for child in root.children:
            if child.type==self.Class:
                class_code = code[
                    child.start_byte:child.end_byte
                ].decode("utf-8")

                lines = class_code.count("\n") + 1
                if lines <= 50:

                    chunks.append({
                        "type": "class",
                        "language": language,
                        "start_line": child.start_point.row + 1,
                        "end_line": child.end_point.row + 1,
                        "code": class_code,
                        "file_name":file_name,
                        "file_path":file_path,
                    })

                # Large class → methods
                else:

                    body = child.child_by_field_name("body")

                    if body:

                        for method in body.named_children:

                            if method.type == self.method:

                                method_code = code[
                                    method.start_byte:method.end_byte
                                ].decode("utf-8")

                                chunks.append({
                                    "type": "method",
                                    "language": language,
                                    "start_line": method.start_point.row + 1,
                                    "end_line": method.end_point.row + 1,
                                    "code": method_code,
                                    "file_name":file_name,
                                    "file_path":file_path,
                                })
            if self.function and child.type == self.function:

                function_code = code[
                    child.start_byte:child.end_byte
                ].decode("utf-8")

                chunks.append({
                    "type": "function",
                    "language": language,
                    "start_line": child.start_point.row + 1,
                    "end_line": child.end_point.row + 1,
                    "code": function_code,
                    "file_name":file_name,
                    "file_path":file_path,
                })
        return chunks

