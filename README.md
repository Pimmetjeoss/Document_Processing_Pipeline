# Document Processing Pipeline

Een krachtige RAG (Retrieval-Augmented Generation) pipeline voor het verwerken van documenten met Milvus/Zilliz Cloud vector database en OpenAI embeddings.

## 🚀 Functies

- **Multi-format document ondersteuning**: Verwerkt PDF, DOCX, TXT, MD, CSV, JSON, HTML, XML, en meer
- **Intelligente chunking**: Gebruikt hiërarchische chunking voor optimale tekstsegmentatie
- **Vector opslag**: Integreert met Milvus/Zilliz Cloud voor schaalbare vector database opslag
- **AI-powered search**: Gebruikt OpenAI embeddings voor semantische zoekfunctionaliteit
- **Configureerbaar**: Volledig configureerbaar via environment variabelen

## 📋 Vereisten

- Python 3.8+
- OpenAI API key
- Zilliz Cloud account (gratis tier beschikbaar)

## 🛠️ Installatie

1. **Clone de repository**
```bash
git clone https://github.com/Pimmetjeoss/Document_Processing_Pipeline.git
cd Document_Processing_Pipeline
```

2. **Installeer dependencies**
```bash
pip install -r requirements.txt
```

3. **Configureer environment variabelen**

Maak een `.env` bestand in de project root:

```env
# OpenAI configuratie
OPENAI_API_KEY=your_openai_api_key_here

# Zilliz Cloud configuratie
ZILLIZ_ENDPOINT=your_zilliz_endpoint_here
ZILLIZ_TOKEN=your_zilliz_token_here

# Optioneel: Collection naam (standaard: my_rag_collection)
COLLECTION_NAME=my_rag_collection
```

### Zilliz Cloud Setup

1. Ga naar [Zilliz Cloud](https://cloud.zilliz.com)
2. Maak een gratis account aan
3. Maak een nieuwe cluster aan
4. Kopieer de endpoint URL en genereer een API token
5. Voeg deze toe aan je `.env` bestand

## 📂 Project Structuur

```
Document_Processing_Pipeline/
│
├── rag_milvus.py           # Hoofdscript voor document processing en RAG
├── simple_converter.py     # Utility voor eenvoudige document conversie
├── requirements.txt        # Python dependencies
├── .env                   # Environment variabelen (niet in git)
├── .gitignore            # Git ignore configuratie
└── README.md             # Deze file
```

## 🚀 Gebruik

### Basis gebruik

1. **Plaats documenten in de `docs/` folder**
```bash
mkdir docs
# Plaats je PDF, DOCX, TXT, of andere documenten hier
```

2. **Verwerk documenten en bouw de vector database**
```bash
python rag_milvus.py
```

Het script zal:
- Alle documenten in de `docs/` folder verwerken
- Tekst extraheren en in chunks opdelen
- Embeddings genereren met OpenAI
- Chunks opslaan in Milvus/Zilliz Cloud

### Zoeken in documenten

```python
from rag_milvus import search

# Zoek naar relevante chunks
question = "Wat zijn de belangrijkste features?"
results = search(question, limit=5)

for text, score in results:
    print(f"Score: {score:.4f}")
    print(f"Text: {text[:200]}...")
    print("-" * 50)
```

### Document Converter

Voor eenvoudige document conversie zonder vector database:

```bash
python simple_converter.py
```

Dit converteert documenten naar markdown formaat voor verdere verwerking.

## 🔧 Configuratie

### Ondersteunde bestandsformaten

- **Documenten**: PDF, DOCX, PPTX, XLSX
- **Tekst**: TXT, MD, RST
- **Data**: CSV, JSON
- **Web**: HTML, XML
- **Code**: Python, JavaScript, en meer

### Chunking Parameters

De pipeline gebruikt intelligente chunking met:
- Maximale chunk grootte: 1024 tokens
- Chunk overlap: 256 tokens
- Hiërarchische structuur behoud

### Vector Database Schema

De Milvus collection gebruikt:
- **id**: Unieke identifier voor elke chunk
- **vector**: 1536-dimensionale embedding vector (OpenAI text-embedding-3-small)
- **text**: Originele tekst content

## 🤝 Bijdragen

Bijdragen zijn welkom! Voel je vrij om:
- Issues aan te maken voor bugs of feature requests
- Pull requests in te dienen voor verbeteringen
- Documentatie te verbeteren

## 📜 Licentie

Dit project is open source en beschikbaar onder de MIT License.

## 🔒 Beveiliging

- **Bewaar nooit API keys in code**: Gebruik altijd environment variabelen
- **Voeg `.env` toe aan `.gitignore`**: Voorkom het per ongeluk committen van credentials
- **Gebruik secret scanning**: GitHub's push protection voorkomt het pushen van secrets

## 🐛 Troubleshooting

### OPENAI_API_KEY niet gevonden
Zorg ervoor dat je `.env` bestand correct is geconfigureerd en in de project root staat.

### Zilliz Cloud verbindingsfout
- Controleer of je endpoint URL correct is (inclusief https://)
- Verifieer dat je API token geldig is
- Check of je cluster actief is in Zilliz Cloud

### Document processing errors
- Zorg ervoor dat de `docs/` folder bestaat
- Controleer of documenten niet corrupt zijn
- Voor grote PDF's kan processing langer duren

## 📞 Contact

Voor vragen of ondersteuning, maak een issue aan op [GitHub](https://github.com/Pimmetjeoss/Document_Processing_Pipeline/issues).

---

*Gebouwd met ❤️ met behulp van Docling, Milvus, en OpenAI*