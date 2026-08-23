import csv
import os
import re
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

CHROMA_PATH = PROJECT_DIR / "chroma_db"
DATA_DIR = PROJECT_DIR / "data" / "documents"

COLLECTION_NAME = "nexusflow_documentos"

EMBEDDING_MODEL = "gemini-embedding-001"

load_dotenv(PROJECT_DIR / ".env")

GENERATION_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


# ============================================================
# CLASSE PRINCIPAL
# ============================================================

class NexusFlowRAG:

    def __init__(self):

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY não encontrada. "
                "Configure a variável no arquivo .env."
            )

        self.gemini_client = genai.Client(
            api_key=api_key
        )

        # ----------------------------------------------------
        # CHROMADB
        # ----------------------------------------------------

        chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        try:
            self.collection = chroma_client.get_collection(
                name=COLLECTION_NAME
            )

        except Exception as error:

            raise RuntimeError(
                "Base vetorial não encontrada. "
                "Execute primeiro:\n\n"
                "python -m scripts.ingest_documents"
            ) from error

        # ----------------------------------------------------
        # CAMINHO DO CSV
        # ----------------------------------------------------

        self.csv_path = DATA_DIR / "pedidos.csv"


    # ========================================================
    # EMBEDDING
    # ========================================================

    def _generate_embedding(
        self,
        text: str
    ) -> list[float]:

        response = self.gemini_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )

        return response.embeddings[0].values


    # ========================================================
    # IDENTIFICAR PEDIDO
    # ========================================================

    def _extract_order_id(
        self,
        question: str
    ) -> str | None:

        match = re.search(
            r"\bNF-\d{4}\b",
            question.upper()
        )

        if match:
            return match.group(0)

        return None


    # ========================================================
    # BUSCA EXATA NO CSV
    # ========================================================

    def _find_order(
        self,
        order_id: str
    ) -> dict | None:

        if not self.csv_path.exists():
            return None

        try:

            with open(
                self.csv_path,
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as file:

                reader = csv.DictReader(file)

                for row in reader:

                    if (
                        row.get("id_pedido", "")
                        .strip()
                        .upper()
                        == order_id
                    ):
                        return row

        except Exception as error:

            print(
                f"Erro ao consultar pedidos.csv: {error}"
            )

        return None


    # ========================================================
    # FORMATAR RESPOSTA DO PEDIDO
    # ========================================================

    def _answer_order_question(
        self,
        question: str,
        order: dict
    ) -> tuple[str, list[dict]]:

        order_id = order.get(
            "id_pedido",
            "Não informado"
        )

        status = order.get(
            "status",
            "Não informado"
        )

        cliente = order.get(
            "cliente",
            "Não informado"
        )

        cidade = order.get(
            "cidade",
            "Não informado"
        )

        estado = order.get(
            "estado",
            "Não informado"
        )

        transportadora = order.get(
            "transportadora",
            "Não informado"
        )

        data_pedido = order.get(
            "data_pedido",
            "Não informado"
        )

        data_envio = order.get(
            "data_envio",
            "Não informado"
        )

        data_entrega = order.get(
            "data_entrega",
            ""
        )

        prazo = order.get(
            "prazo_dias",
            "Não informado"
        )

        frete = order.get(
            "valor_frete",
            "Não informado"
        )

        pergunta = question.lower()


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if "status" in pergunta:

            answer = (
                f"O status do pedido **{order_id}** é "
                f"**{status}**."
            )


        # ----------------------------------------------------
        # RASTREAR / RASTREAMENTO
        # ----------------------------------------------------

        elif (
            "rastrear" in pergunta
            or "rastreamento" in pergunta
            or "rastreio" in pergunta
        ):

            answer = (
                f"O pedido **{order_id}** está com status "
                f"**{status}**.\n\n"
                f"**Transportadora:** {transportadora}\n\n"
                f"**Data de envio:** {data_envio}\n\n"
                f"**Prazo:** {prazo} dias"
            )

            if data_entrega:

                answer += (
                    f"\n\n**Data de entrega:** "
                    f"{data_entrega}"
                )


        # ----------------------------------------------------
        # TRANSPORTADORA
        # ----------------------------------------------------

        elif "transportadora" in pergunta:

            answer = (
                f"A transportadora do pedido "
                f"**{order_id}** é **{transportadora}**."
            )


        # ----------------------------------------------------
        # CLIENTE
        # ----------------------------------------------------

        elif (
            "cliente" in pergunta
            or "quem fez" in pergunta
        ):

            answer = (
                f"O cliente do pedido **{order_id}** "
                f"é **{cliente}**."
            )


        # ----------------------------------------------------
        # CIDADE / LOCALIZAÇÃO
        # ----------------------------------------------------

        elif (
            "cidade" in pergunta
            or "localização" in pergunta
            or "localizacao" in pergunta
        ):

            answer = (
                f"O pedido **{order_id}** está associado "
                f"à cidade de **{cidade} - {estado}**."
            )


        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        elif (
            "data do pedido" in pergunta
            or "quando foi pedido" in pergunta
        ):

            answer = (
                f"O pedido **{order_id}** foi realizado "
                f"em **{data_pedido}**."
            )


        # ----------------------------------------------------
        # FRETE
        # ----------------------------------------------------

        elif (
            "frete" in pergunta
            or "valor do frete" in pergunta
        ):

            answer = (
                f"O valor do frete do pedido "
                f"**{order_id}** é **R$ {frete}**."
            )


        # ----------------------------------------------------
        # ENTREGA
        # ----------------------------------------------------

        elif (
            "entrega" in pergunta
            or "entregue" in pergunta
        ):

            answer = (
                f"O pedido **{order_id}** está com status "
                f"**{status}**.\n\n"
                f"**Prazo:** {prazo} dias."
            )

            if data_entrega:

                answer += (
                    f"\n\n**Data de entrega:** "
                    f"{data_entrega}"
                )


        # ----------------------------------------------------
        # RESPOSTA COMPLETA
        # ----------------------------------------------------

        else:

            answer = (
                f"**Pedido {order_id}**\n\n"
                f"- **Cliente:** {cliente}\n"
                f"- **Cidade:** {cidade} - {estado}\n"
                f"- **Transportadora:** {transportadora}\n"
                f"- **Status:** {status}\n"
                f"- **Data do pedido:** {data_pedido}\n"
                f"- **Data de envio:** {data_envio}\n"
                f"- **Prazo:** {prazo} dias\n"
                f"- **Frete:** R$ {frete}"
            )

            if data_entrega:

                answer += (
                    f"\n- **Data de entrega:** "
                    f"{data_entrega}"
                )


        source = {
            "title": "pedidos.csv",
            "source": "pedidos.csv",
            "category": "Dados operacionais",
            "row": order_id,
        }

        return answer, [source]


    # ========================================================
    # BUSCA SEMÂNTICA
    # ========================================================

    def search_documents(
        self,
        question: str,
        n_results: int = 15
    ) -> dict:

        question_embedding = self._generate_embedding(
            question
        )

        return self.collection.query(
            query_embeddings=[question_embedding],
            n_results=n_results,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )


    # ========================================================
    # IDENTIFICAR PERGUNTA DE POLÍTICA
    # ========================================================

    def _is_policy_question(
        self,
        question: str
    ) -> bool:

        pergunta = question.lower()

        policy_terms = [
            "devolução",
            "devolucao",
            "arrependimento",
            "reembolso",
            "avariado",
            "avaria",
            "defeito",
            "cancelamento",
            "cancelar",
            "extraviado",
            "extravio",
            "tentativas de entrega",
            "tentativa de entrega",
            "tentativa",
            "prazo",
            "alterar endereço",
            "alteração de endereço",
            "alteracao de endereco",
            "endereço",
            "endereco",
            "privacidade",
            "suporte",
            "plano",
            "assinatura",
            "pagamento",
        ]

        return any(
            term in pergunta
            for term in policy_terms
        )


    # ========================================================
    # VERIFICAR SE É PDF
    # ========================================================

    @staticmethod
    def _is_pdf(
        metadata: dict
    ) -> bool:

        tipo = str(
            metadata.get(
                "tipo",
                ""
            )
        ).upper()

        source = str(
            metadata.get(
                "source",
                ""
            )
        ).lower()

        return (
            tipo == "PDF"
            or source.endswith(".pdf")
        )


    # ========================================================
    # TERMOS IMPORTANTES DA PERGUNTA
    # ========================================================

    @staticmethod
    def _question_terms(
        question: str
    ) -> set[str]:

        stopwords = {
            "a", "o", "as", "os",
            "um", "uma",
            "uns", "umas",
            "de", "da", "do",
            "das", "dos",
            "em", "no", "na",
            "nos", "nas",
            "por", "para",
            "com", "sem",
            "sobre",
            "é", "e", "ou",
            "que", "qual",
            "quais", "como",
            "quando", "onde",
            "posso", "pode",
            "são", "ser",
            "foi", "depois",
            "mais", "se",
            "ao", "aos",
            "às",
            "meu", "minha",
            "me",
            "seu", "sua",
            "funciona",
        }

        words = re.findall(
            r"[a-záàâãéêíóôõúç0-9]+",
            question.lower()
        )

        return {
            word
            for word in words
            if len(word) >= 3
            and word not in stopwords
        }


    # ========================================================
    # RELEVÂNCIA TEXTUAL
    # ========================================================

    def _text_relevance(
        self,
        question: str,
        document: str
    ) -> float:

        question_terms = self._question_terms(
            question
        )

        if not question_terms:
            return 0.0

        normalized_document = document.lower()

        matched = sum(
            1
            for term in question_terms
            if term in normalized_document
        )

        return matched / len(
            question_terms
        )


    # ========================================================
    # FILTRAR E RANQUEAR RESULTADOS
    # ========================================================

    def _filter_results(
        self,
        results: dict,
        question: str
    ) -> tuple[list, list, list]:

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        if not documents:

            return [], [], []

        is_policy_question = (
            self._is_policy_question(
                question
            )
        )

        candidates = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):

            distance = float(distance)

            # ------------------------------------------------
            # Limite amplo para evitar perder documentos
            # potencialmente relevantes.
            # ------------------------------------------------

            if distance > 1.50:
                continue

            is_pdf = self._is_pdf(
                metadata
            )

            textual_score = (
                self._text_relevance(
                    question,
                    str(document)
                )
            )

            # ------------------------------------------------
            # Similaridade semântica
            # ------------------------------------------------

            semantic_score = max(
                0.0,
                1.0 - distance / 1.50
            )

            # ------------------------------------------------
            # Score combinado
            # ------------------------------------------------

            score = (
                semantic_score * 0.60
                + textual_score * 0.40
            )

            # PDF ganha prioridade em perguntas de política.
            if is_policy_question and is_pdf:
                score += 0.15

            candidates.append(
                (
                    score,
                    document,
                    metadata,
                    distance,
                )
            )


        if not candidates:

            return [], [], []


        # ----------------------------------------------------
        # Ordenar melhores resultados primeiro
        # ----------------------------------------------------

        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )


        # ----------------------------------------------------
        # Para perguntas de política, priorizar PDFs.
        # ----------------------------------------------------

        if is_policy_question:

            pdf_candidates = [
                item
                for item in candidates
                if self._is_pdf(
                    item[2]
                )
            ]

            if pdf_candidates:

                candidates = pdf_candidates


        # ----------------------------------------------------
        # Limitar contexto aos melhores resultados
        # ----------------------------------------------------

        candidates = candidates[:8]


        documents = [
            item[1]
            for item in candidates
        ]

        metadatas = [
            item[2]
            for item in candidates
        ]

        distances = [
            item[3]
            for item in candidates
        ]

        return (
            documents,
            metadatas,
            distances,
        )


    # ========================================================
    # CONSTRUIR FONTES
    # ========================================================

    def _build_sources(
        self,
        metadatas: list
    ) -> list[dict]:

        sources = []

        for metadata in metadatas:

            source = metadata.get(
                "source",
                "Documento desconhecido"
            )

            tipo = str(
                metadata.get(
                    "tipo",
                    ""
                )
            ).upper()

            categoria = metadata.get(
                "categoria",
                metadata.get(
                    "category",
                    "Documentos"
                )
            )


            # ------------------------------------------------
            # PDF
            # ------------------------------------------------

            if (
                tipo == "PDF"
                or str(
                    source
                ).lower().endswith(".pdf")
            ):

                page = metadata.get(
                    "page",
                    metadata.get(
                        "pagina",
                        ""
                    )
                )

                item = {
                    "title": source,
                    "source": source,
                    "category": categoria,
                }

                if page not in ("", None):

                    item["page"] = str(
                        page
                    )


            # ------------------------------------------------
            # CSV
            # ------------------------------------------------

            else:

                row = metadata.get(
                    "row",
                    metadata.get(
                        "id_pedido",
                        ""
                    )
                )

                item = {
                    "title": source,
                    "source": source,
                    "category": categoria,
                }

                if row not in ("", None):

                    item["row"] = str(
                        row
                    )


            if item not in sources:

                sources.append(
                    item
                )


        return sources


    # ========================================================
    # FALLBACK
    # ========================================================

    def _build_fallback(
        self,
        documents: list,
        metadatas: list
    ) -> str:

        if not documents:

            return (
                "Não encontrei essa informação nos "
                "documentos disponíveis."
            )

        lines = [
            "A informação foi localizada na base de "
            "conhecimento, mas o serviço de geração "
            "de respostas está temporariamente "
            "indisponível.",
            "",
            "**Trecho encontrado:**",
            "",
        ]


        for document, metadata in zip(
            documents[:3],
            metadatas[:3]
        ):

            source = metadata.get(
                "source",
                "Documento"
            )

            text = " ".join(
                str(document).split()
            )

            if len(text) > 700:

                text = (
                    text[:700]
                    + "..."
                )

            lines.append(
                f"- **{source}:** {text}"
            )


        return "\n".join(
            lines
        )


    # ========================================================
    # CONSTRUIR CONTEXTO
    # ========================================================

    def _build_context(
        self,
        documents: list,
        metadatas: list
    ) -> str:

        context_parts = []

        for index, (
            document,
            metadata
        ) in enumerate(
            zip(
                documents[:6],
                metadatas[:6]
            ),
            start=1
        ):

            source = metadata.get(
                "source",
                "Documento desconhecido"
            )

            page = metadata.get(
                "page",
                metadata.get(
                    "pagina",
                    ""
                )
            )

            if page not in (
                "",
                None
            ):

                reference = (
                    f"{source}, "
                    f"página {page}"
                )

            else:

                reference = source


            context_parts.append(
                f"[Fonte {index}: "
                f"{reference}]\n"
                f"{document}"
            )


        return "\n\n".join(
            context_parts
        )


    # ========================================================
    # RESPONDER PERGUNTA
    # ========================================================

    def answer_question(
        self,
        question: str
    ) -> tuple[str, list[dict]]:

        question = question.strip()

        if not question:

            return (
                "Digite uma pergunta para consultar "
                "a base de conhecimento.",
                [],
            )


        # ====================================================
        # 1. PEDIDO ESPECÍFICO
        # ====================================================

        order_id = self._extract_order_id(
            question
        )

        if order_id:

            order = self._find_order(
                order_id
            )

            if order:

                return (
                    self._answer_order_question(
                        question,
                        order
                    )
                )

            return (
                f"Não encontrei o pedido "
                f"**{order_id}** "
                f"nos dados operacionais disponíveis.",
                [],
            )


        # ====================================================
        # 2. BUSCA SEMÂNTICA
        # ====================================================

        try:

            results = self.search_documents(
                question,
                n_results=15
            )

        except Exception as error:

            print(
                f"Erro na busca vetorial: {error}"
            )

            return (
                "Não foi possível consultar a base "
                "de conhecimento no momento.",
                [],
            )


        documents, metadatas, distances = (
            self._filter_results(
                results,
                question
            )
        )


        # ====================================================
        # 3. NENHUM RESULTADO
        # ====================================================

        if not documents:

            return (
                "Não encontrei essa informação nos "
                "documentos disponíveis.",
                [],
            )


        # ====================================================
        # 4. FONTES
        # ====================================================

        sources = self._build_sources(
            metadatas
        )


        # ====================================================
        # 5. CONTEXTO
        # ====================================================

        context = self._build_context(
            documents,
            metadatas
        )


        # ====================================================
        # 6. PROMPT
        # ====================================================

        prompt = f"""
Você é o NexusFlow AI, assistente da plataforma SaaS NexusFlow.

Sua função é responder perguntas utilizando EXCLUSIVAMENTE
o contexto fornecido abaixo.

REGRAS OBRIGATÓRIAS:

1. Use somente informações presentes no contexto.
2. Não invente informações.
3. Não use conhecimento externo.
4. Não complete informações que não estejam no contexto.
5. Se o contexto realmente não responder à pergunta,
   responda exatamente:

"Não encontrei essa informação nos documentos disponíveis."

6. Responda em português do Brasil.
7. Seja objetivo, claro e profissional.
8. Preserve exatamente valores, prazos, quantidades
   e condições presentes nos documentos.
9. Se houver uma regra ou procedimento no documento,
   explique de forma clara e organizada.
10. Não mencione o funcionamento interno do RAG.
11. Não diga que consultou conhecimentos externos.
12. Não transforme dados de pedidos em políticas gerais.
13. Se houver mais de uma fonte relevante, combine
    somente informações explicitamente presentes.
14. Não invente informações para preencher lacunas.
15. Se a pergunta solicitar prazo, quantidade,
    condição ou procedimento, procure especificamente
    essa informação no contexto.

PERGUNTA:

{question}

CONTEXTO:

{context}

Agora responda à pergunta usando exclusivamente
o contexto.
"""


        # ====================================================
        # 7. GEMINI
        # ====================================================

        try:

            response = (
                self.gemini_client
                .models
                .generate_content(
                    model=GENERATION_MODEL,
                    contents=prompt,
                )
            )

            answer = (
                response.text.strip()
                if response.text
                else ""
            )


            if not answer:

                return (
                    self._build_fallback(
                        documents,
                        metadatas
                    ),
                    sources,
                )


            return (
                answer,
                sources
            )


        except Exception as error:

            print(
                f"Gemini indisponível: {error}"
            )

            return (
                self._build_fallback(
                    documents,
                    metadatas
                ),
                sources,
            )


# ============================================================
# FUNÇÃO DE COMPATIBILIDADE
# ============================================================

def responder_pergunta(
    pergunta: str
) -> tuple[str, list[dict]]:

    rag = NexusFlowRAG()

    return rag.answer_question(
        pergunta
    )