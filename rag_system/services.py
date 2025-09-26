import logging
from django.conf import settings
from .models import Document, DocumentChunk, DocumentCollection

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    def __init__(self):
        self.text_splitter = None
        self.embeddings = None

    def _init_heavy(self):
        if not self.text_splitter:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        if not self.embeddings:
            from sentence_transformers import SentenceTransformer
            try:
                self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.error(f"Error loading embeddings: {str(e)}")
                self.embeddings = None

    def process_document(self, document):
        self._init_heavy()
        from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
        import chromadb
        try:
            # Extract text
            text_content = self._extract_text(document)
            if not text_content:
                return False

            # Split into chunks
            chunks = self.text_splitter.split_text(text_content)
            if not chunks:
                return False

            # Create Chroma collection
            collection_name = f"user_{document.collection.user.id}_col_{document.collection.id}"
            document.chroma_collection_name = collection_name
            client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIRECTORY))
            chroma_collection = client.get_or_create_collection(name=collection_name)

            # Save chunks and embeddings
            for i, chunk in enumerate(chunks):
                DocumentChunk.objects.create(document=document, content=chunk, chunk_index=i)
                if self.embeddings:
                    try:
                        embedding = self.embeddings.encode([chunk])[0].tolist()
                        chroma_collection.add(
                            documents=[chunk],
                            embeddings=[embedding],
                            metadatas=[{
                                "document_id": str(document.id),
                                "chunk_index": i,
                                "filename": document.filename
                            }],
                            ids=[f"{document.id}_{i}"]
                        )
                    except Exception as e:
                        logger.warning(f"Embedding generation error: {str(e)}")

            document.chunk_count = len(chunks)
            document.processed = True
            document.save()
            return True
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return False

    def _extract_text(self, document):
        try:
            from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
            file_path = document.file_path.path
            if document.file_type == 'pdf':
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                return "\n".join([page.page_content for page in pages])
            elif document.file_type in ['docx', 'doc']:
                loader = Docx2txtLoader(file_path)
                doc = loader.load()
                return doc[0].page_content if doc else ""
            elif document.file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
        return ""


class RAGService:
    def __init__(self):
        import openai
        self.openai = openai
        self.embeddings = None

    def _init_embeddings(self):
        if not self.embeddings:
            from sentence_transformers import SentenceTransformer
            try:
                self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.error(f"Error loading embeddings: {str(e)}")
                self.embeddings = None

    def query_documents(self, query, collection_id, user):
        self._init_embeddings()
        import chromadb
        try:
            collection = DocumentCollection.objects.get(id=collection_id, user=user)
            if not collection.documents.filter(processed=True).exists():
                return "No processed documents found.", []

            client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIRECTORY))
            chroma_collection_name = f"user_{user.id}_col_{collection_id}"
            chroma_collection = client.get_collection(name=chroma_collection_name)

            if self.embeddings:
                query_embedding = self.embeddings.encode([query])[0].tolist()
                results = chroma_collection.query(query_embeddings=[query_embedding], n_results=5)
            else:
                results = chroma_collection.query(query_texts=[query], n_results=5)

            relevant_chunks = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []

            if not relevant_chunks:
                return "No relevant information found.", []

            context = "\n\n".join(relevant_chunks[:3])
            prompt = f"""Based on the following context, answer the question.

Context: {context}

Question: {query}

Answer:"""

            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )

            answer = response.choices[0].message.content
            sources = []
            seen_files = set()
            for metadata in metadatas[:3]:
                filename = metadata.get('filename', 'Unknown')
                if filename not in seen_files:
                    sources.append({
                        'filename': filename,
                        'chunk_index': metadata.get('chunk_index', 0)
                    })
                    seen_files.add(filename)

            return answer, sources

        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            return f"Error querying documents: {str(e)}", []
