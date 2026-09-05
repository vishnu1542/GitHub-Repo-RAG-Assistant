from langchain_core.documents import Document

class chunking:
    def get_document_chunks(self,chunks):
        documents=[]
        for chunk in chunks:
            documents.append(Document(
                page_content=chunk["code"],
                metadata={
                    "type":chunk["type"],
                    "language":chunk["language"],
                    "start_line":chunk["start_line"],
                    "end_line":chunk["end_line"],
                    "file_path": chunk["file_path"],
                    "file_name": chunk["file_name"]
                }
                
            )
            )