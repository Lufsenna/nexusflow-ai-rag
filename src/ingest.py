import csv
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / "data" / "documents"

DB_DIR = PROJECT_DIR / "chroma_db"

COLLECTION_NAME = "nexusflow_documentos"

EMBEDDING_MODEL = "gemini-embedding-001"


load_dotenv(PROJECT_DIR / ".env")


# ============================================================
# CORREÇÃO DE ENCODING
# ============================================================

def corrigir_encoding(texto: str) -> str:

    if not texto:
        return ""

    try:

        if (
            "Ã" in texto
            or "Â" in texto
            or "â" in texto
        ):
            texto = texto.encode(
                "latin1"
            ).decode(
                "utf-8"
            )

    except (
        UnicodeEncodeError,
        UnicodeDecodeError
    ):
        pass

    return texto


# ============================================================
# CARREGAMENTO DOS DOCUMENTOS
# ============================================================

def carregar_documentos():

    documentos = []

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    pdf_files = sorted(
        DATA_DIR.glob("*.pdf")
    )

    for arquivo in pdf_files:

        try:

            loader = PyPDFLoader(
                str(arquivo)
            )

            docs = loader.load()

            for doc in docs:

                doc.page_content = corrigir_encoding(
                    doc.page_content
                ).strip()

                doc.metadata.update(
                    {
                        "source": arquivo.name,
                        "categoria": "documentacao",
                        "tipo": "PDF",
                    }
                )

            documentos.extend(docs)

            print(
                f"PDF carregado: {arquivo.name} "
                f"({len(docs)} páginas)"
            )

        except Exception as erro:

            print(
                f"ERRO no PDF {arquivo.name}: {erro}"
            )


    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_files = sorted(
        DATA_DIR.glob("*.csv")
    )

    for arquivo in csv_files:

        try:

            # Tentamos UTF-8 primeiro
            try:

                with open(
                    arquivo,
                    "r",
                    encoding="utf-8-sig",
                    newline=""
                ) as file:

                    reader = csv.DictReader(file)

                    rows = list(reader)

            except UnicodeDecodeError:

                with open(
                    arquivo,
                    "r",
                    encoding="latin-1",
                    newline=""
                ) as file:

                    reader = csv.DictReader(file)

                    rows = list(reader)


            print(
                f"CSV carregado: {arquivo.name} "
                f"({len(rows)} registros)"
            )


            # ------------------------------------------------
            # Cada linha do CSV vira um documento separado
            # ------------------------------------------------

            for numero_linha, row in enumerate(
                rows,
                start=2
            ):

                row = {
                    chave: corrigir_encoding(
                        valor or ""
                    )
                    for chave, valor in row.items()
                }


                texto = "\n".join(
                    f"{chave}: {valor}"
                    for chave, valor in row.items()
                )


                from langchain_core.documents import Document


                doc = Document(
                    page_content=texto,
                    metadata={
                        "source": arquivo.name,
                        "categoria": "dados_operacionais",
                        "tipo": "CSV",
                        "row": numero_linha,
                        "id_pedido": row.get(
                            "id_pedido",
                            ""
                        ),
                    }
                )


                documentos.append(doc)


        except Exception as erro:

            print(
                f"ERRO no CSV {arquivo.name}: {erro}"
            )


    return documentos


# ============================================================
# GERAR EMBEDDINGS
# ============================================================

def gerar_embeddings(
    client,
    textos: list[str]
) -> list[list[float]]:

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=textos,
    )

    return [
        item.values
        for item in response.embeddings
    ]


# ============================================================
# CRIAR BANCO VETORIAL
# ============================================================

def criar_banco_vetorial():

    print(
        "\n=========================================="
    )

    print(
        "🚀 INICIANDO INDEXAÇÃO NEXUSFLOW"
    )

    print(
        "==========================================\n"
    )


    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "GOOGLE_API_KEY não encontrada. "
            "Configure-a no arquivo .env."
        )


    # --------------------------------------------------------
    # VERIFICA PASTA
    # --------------------------------------------------------

    if not DATA_DIR.exists():

        raise FileNotFoundError(
            f"Pasta não encontrada: {DATA_DIR}"
        )


    # --------------------------------------------------------
    # CARREGA DOCUMENTOS
    # --------------------------------------------------------

    documentos = carregar_documentos()


    if not documentos:

        raise ValueError(
            "Nenhum documento foi encontrado."
        )


    print(
        f"\n📄 Total de documentos carregados: "
        f"{len(documentos)}"
    )


    # --------------------------------------------------------
    # CHUNKING
    #
    # PDFs são divididos.
    # CSV permanece em registros individuais.
    # --------------------------------------------------------

    separador = RecursiveCharacterTextSplitter(

        chunk_size=900,

        chunk_overlap=150,

        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            " ",
            ""
        ],
    )


    chunks = []


    for documento in documentos:

        # CSV não precisa ser quebrado
        if documento.metadata.get(
            "tipo"
        ) == "CSV":

            chunks.append(
                documento
            )

        else:

            partes = separador.split_documents(
                [documento]
            )

            chunks.extend(
                partes
            )


    print(
        f"🧩 Total de chunks: {len(chunks)}"
    )


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    client = genai.Client(
        api_key=api_key
    )


    textos = [
        chunk.page_content
        for chunk in chunks
    ]


    print(
        "\n🧠 Gerando embeddings..."
    )


    embeddings = gerar_embeddings(
        client,
        textos
    )


    # --------------------------------------------------------
    # CHROMADB
    # --------------------------------------------------------

    chroma_client = chromadb.PersistentClient(
        path=str(DB_DIR)
    )


    # IMPORTANTE:
    # Recria a coleção para eliminar embeddings antigos
    # e documentos incorretos.

    try:

        chroma_client.delete_collection(
            name=COLLECTION_NAME
        )

        print(
            "🗑️ Coleção antiga removida."
        )

    except Exception:

        pass


    collection = chroma_client.create_collection(

        name=COLLECTION_NAME,

        metadata={
            "hnsw:space": "cosine"
        },
    )


    # --------------------------------------------------------
    # IDS E METADADOS
    # --------------------------------------------------------

    ids = []

    metadados = []


    for indice, chunk in enumerate(
        chunks
    ):

        source = chunk.metadata.get(
            "source",
            "arquivo"
        )

        page = chunk.metadata.get(
            "page",
            0
        )

        tipo = chunk.metadata.get(
            "tipo",
            "documento"
        )

        row = chunk.metadata.get(
            "row",
            0
        )


        if tipo == "CSV":

            identificador = (
                f"{source}_linha_{row}"
            )

        else:

            identificador = (
                f"{source}_pagina_{page}"
                f"_chunk_{indice}"
            )


        ids.append(
            identificador
        )


        metadados.append(
            {
                chave: str(valor)
                for chave, valor
                in chunk.metadata.items()
            }
        )


    # --------------------------------------------------------
    # SALVA NO CHROMADB
    # --------------------------------------------------------

    collection.add(

        ids=ids,

        documents=textos,

        embeddings=embeddings,

        metadatas=metadados,
    )


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print(
        "\n=========================================="
    )

    print(
        "✅ INDEXAÇÃO CONCLUÍDA!"
    )

    print(
        "=========================================="
    )

    print(
        f"📄 Documentos: {len(documentos)}"
    )

    print(
        f"🧩 Chunks: {len(chunks)}"
    )

    print(
        f"📚 Registros no ChromaDB: "
        f"{collection.count()}"
    )

    print(
        f"💾 Banco: {DB_DIR}"
    )

    print(
        "==========================================\n"
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    criar_banco_vetorial()