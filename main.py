from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os
from pathlib import Path
from tqdm import tqdm

# Import existing functions from rag_milvus.py
from rag_milvus import emb_text, milvus_client, collection_name

# Import document processing components
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling_core.transforms.chunker import HierarchicalChunker

# FastAPI setup
app = FastAPI(title="Simple RAG API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize document processing components (reuse existing setup)
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=StandardPdfPipeline,
            backend=PyPdfiumDocumentBackend
        ),
        InputFormat.DOCX: WordFormatOption(
            pipeline_cls=SimplePipeline
        )
    }
)
chunker = HierarchicalChunker(max_tokens=256)

# Ensure collection exists (don't drop existing data)
def ensure_collection():
    if not milvus_client.has_collection(collection_name):
        milvus_client.create_collection(
            collection_name=collection_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric_type="IP",
            consistency_level="Bounded"
        )

# Initialize collection at startup
ensure_collection()

class SearchRequest(BaseModel):
    question: str
    limit: int = 3

@app.get("/")
async def root():
    return {"status": "RAG API is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document"""
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files allowed")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process document (adapted from existing process_documents logic)
        print(f"Processing {file.filename}...")
        doc = converter.convert(tmp_path).document
        chunks = list(chunker.chunk(doc))
        
        # Generate embeddings and prepare data
        data = []
        chunk_id = 0
        
        for chunk in tqdm(chunks, desc="Embedding chunks"):
            embedding = emb_text(chunk.text)
            data.append({
                "id": chunk_id,
                "vector": embedding,
                "text": chunk.text
            })
            chunk_id += 1
        
        # Insert into Milvus
        if data:
            result = milvus_client.insert(collection_name=collection_name, data=data)
            print(f"Inserted {result['insert_count']} chunks into Milvus")
            
            return {
                "message": f"Processed {result['insert_count']} chunks",
                "filename": file.filename,
                "chunks_count": len(chunks)
            }
        else:
            raise HTTPException(status_code=400, detail="No content could be extracted from file")
            
    except Exception as e:
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/search")
async def search(request: SearchRequest):
    """Search in the knowledge base"""
    try:
        # Use existing search logic from rag_milvus.py
        search_res = milvus_client.search(
            collection_name=collection_name,
            data=[emb_text(request.question)],
            limit=request.limit,
            search_params={"metric_type": "IP", "params": {}},
            output_fields=["text"]
        )
        
        results = [(res["entity"]["text"], res["distance"]) for res in search_res[0]]
        return {"results": results}
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get collection statistics"""
    try:
        stats = milvus_client.get_collection_stats(collection_name=collection_name)
        return {"collection_name": collection_name, "stats": stats}
    except Exception as e:
        return {"collection_name": collection_name, "error": str(e)}