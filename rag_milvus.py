import os
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from docling_core.transforms.chunker import HierarchicalChunker
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from openai import OpenAI
from pymilvus import MilvusClient

# Load environment variables
load_dotenv(override=True)  # Force reload of .env

# Setup
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")
    
openai_client = OpenAI(api_key=api_key)

# Cloud-only Milvus client (Zilliz Cloud)
zilliz_endpoint = os.getenv("ZILLIZ_ENDPOINT")
zilliz_token = os.getenv("ZILLIZ_TOKEN")

if not zilliz_endpoint or not zilliz_token:
    print("Error: Zilliz Cloud credentials not found!")
    print("Please configure in .env file:")
    print("  ZILLIZ_ENDPOINT=your_endpoint")
    print("  ZILLIZ_TOKEN=your_token")
    print("\nGet these from https://cloud.zilliz.com")
    exit(1)

milvus_client = MilvusClient(
    uri=zilliz_endpoint,
    token=zilliz_token
)

collection_name = os.getenv("COLLECTION_NAME", "my_rag_collection")

def emb_text(text):
    return (
        openai_client.embeddings.create(input=text, model="text-embedding-3-small")
        .data[0]
        .embedding
    )

def process_documents():
    # Initialize converters with format options
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
    chunker = HierarchicalChunker(max_tokens=256)  # Small chunks for precise retrieval
    
    # Find PDF and DOCX files
    current_dir = Path('.')
    files = list(current_dir.glob('*.pdf')) + list(current_dir.glob('*.docx'))
    
    if not files:
        print("No PDF or DOCX files found in current directory")
        return
    
    print(f"Found {len(files)} documents")
    
    # Setup Milvus collection (only create if it doesn't exist)
    if not milvus_client.has_collection(collection_name):
        milvus_client.create_collection(
            collection_name=collection_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric_type="IP",
            consistency_level="Bounded"  # Better for cloud
        )
    
    # Get current collection stats to generate unique IDs
    try:
        stats = milvus_client.get_collection_stats(collection_name)
        current_count = stats.get('row_count', 0)
    except:
        current_count = 0
    
    # Process each document
    data = []
    chunk_id = current_count
    
    for file_path in files:
        print(f"Processing {file_path.name}...")
        
        try:
            # Convert document
            doc = converter.convert(str(file_path)).document
            
            # Create chunks
            chunks = list(chunker.chunk(doc))
            
            # Generate embeddings and prepare data with progress bar
            for chunk in tqdm(chunks, desc=f"  Embedding chunks", leave=False):
                embedding = emb_text(chunk.text)
                data.append({
                    "id": chunk_id,
                    "vector": embedding,
                    "text": chunk.text
                })
                chunk_id += 1
            
            print(f"  [OK] Created {len(chunks)} chunks")
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    # Insert into Milvus
    if data:
        result = milvus_client.insert(collection_name=collection_name, data=data)
        print(f"\nInserted {result['insert_count']} chunks into Milvus")
    
def search(question, limit=3):
    search_res = milvus_client.search(
        collection_name=collection_name,
        data=[emb_text(question)],
        limit=limit,
        search_params={"metric_type": "IP", "params": {}},
        output_fields=["text"]
    )
    
    results = [(res["entity"]["text"], res["distance"]) for res in search_res[0]]
    return results

if __name__ == "__main__":
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    process_documents()