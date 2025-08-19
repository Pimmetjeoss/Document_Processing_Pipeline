import json
import logging
import os
import warnings
from pathlib import Path
import yaml

# Suppress PyTorch warnings when no GPU is available
warnings.filterwarnings("ignore", message=".*pin_memory.*")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
os.environ["PYTORCH_DISABLE_PIN_MEMORY"] = "1"

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
_log = logging.getLogger(__name__)

def main():
    # Supported file extensions
    supported_extensions = {'.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.html', '.htm', 
                           '.png', '.jpg', '.jpeg', '.md', '.asciidoc', '.csv'}
    
    # Find all supported files in current directory
    current_dir = Path('.')
    input_paths = []
    
    for file_path in current_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            input_paths.append(file_path)
    
    if not input_paths:
        _log.error(f"No supported files found in current directory")
        _log.info(f"Supported formats: {', '.join(supported_extensions)}")
        return
    
    _log.info(f"Found {len(input_paths)} supported files:")
    for path in sorted(input_paths):
        _log.info(f"  - {path}")
    
    # Setup document converter
    doc_converter = DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.IMAGE,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.PPTX,
            InputFormat.ASCIIDOC,
            InputFormat.CSV,
            InputFormat.MD,
        ],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline, 
                backend=PyPdfiumDocumentBackend
            ),
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline
            ),
        },
    )

    # Convert all found files
    try:
        conv_results = doc_converter.convert_all(input_paths)
    except Exception as e:
        _log.error(f"Conversion failed: {e}")
        return

    # Create output directory
    out_path = Path("scratch")
    out_path.mkdir(exist_ok=True)

    # Export results
    chunker = HybridChunker()
    
    for res in conv_results:
        try:
            file_stem = res.input.file.stem
            _log.info(f"Exporting {res.input.file.name}...")
            
            # Export to markdown
            with (out_path / f"{file_stem}.md").open("w", encoding='utf-8') as fp:
                fp.write(res.document.export_to_markdown())

            # Export to JSON
            with (out_path / f"{file_stem}.json").open("w", encoding='utf-8') as fp:
                fp.write(json.dumps(res.document.export_to_dict(), indent=2))

            # Export to YAML
            with (out_path / f"{file_stem}.yaml").open("w", encoding='utf-8') as fp:
                fp.write(yaml.safe_dump(res.document.export_to_dict()))

            # Export chunks
            chunks = list(chunker.chunk(res.document))
            with (out_path / f"{file_stem}_chunks.txt").open("w", encoding='utf-8') as fp:
                for chunk in chunks:
                    fp.write(f"{chunk.text}\n---\n")
            
            _log.info(f"✓ Exported {file_stem} to markdown, JSON, YAML, and chunks ({len(chunks)} chunks)")
            
        except Exception as e:
            _log.error(f"Failed to export {res.input.file.name}: {e}")

    _log.info(f"Conversion completed! Output saved to: {out_path}")

if __name__ == "__main__":
    main()