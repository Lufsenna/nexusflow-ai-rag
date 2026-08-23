from pathlib import Path
from pypdf import PdfReader


def corrigir_encoding(texto: str) -> str:
    """
    Corrige problemas comuns de texto UTF-8 interpretado
    como Latin-1/Windows-1252.
    """

    if not texto:
        return ""

    try:
        if "Ã" in texto or "Â" in texto or "â" in texto:
            texto = texto.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    return texto


def load_pdf_documents(documents_path: str) -> list[dict]:
    """
    Lê todos os PDFs da pasta data/documents.
    Cada página vira um documento com metadados.
    """

    documents = []

    path = Path(documents_path)

    if not path.exists():
        raise FileNotFoundError(
            f"A pasta de documentos não foi encontrada: {documents_path}"
        )

    pdf_files = sorted(path.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            "Nenhum arquivo PDF foi encontrado em data/documents."
        )

    for pdf_file in pdf_files:

        reader = PdfReader(str(pdf_file))

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text() or ""

            text = corrigir_encoding(text).strip()

            if not text:
                continue

            documents.append(
                {
                    "text": text,
                    "metadata": {
                        "source": pdf_file.name,
                        "page": page_number,
                        "categoria": "documentacao",
                        "tipo": "PDF",
                    },
                }
            )

    return documents


def split_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 150
) -> list[str]:
    """
    Divide um texto grande em chunks.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap deve ser menor que chunk_size."
        )

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks