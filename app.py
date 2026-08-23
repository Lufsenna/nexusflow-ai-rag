import time

import streamlit as st

from src.rag import NexusFlowRAG


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="NexusFlow AI",
    page_icon="🚚",
    layout="wide",
)


# ============================================================
# CABEÇALHO
# ============================================================

st.title("🚚 NexusFlow AI")

st.subheader(
    "Assistente inteligente para políticas e operações logísticas"
)

st.info(
    "Faça perguntas sobre entregas, rastreamento, reembolsos, "
    "devoluções, cancelamentos e atendimento. "
    "As respostas são baseadas exclusivamente nos documentos "
    "internos cadastrados."
)


# ============================================================
# CARREGAMENTO DO AGENTE RAG
# ============================================================

@st.cache_resource
def get_rag_agent():
    return NexusFlowRAG()


# ============================================================
# MEMÓRIA DA CONVERSA
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# MENU LATERAL
# ============================================================

with st.sidebar:

    st.header("💡 Exemplos de perguntas")

    example_questions = [
        "Como posso rastrear um pedido?",
        "Quantas tentativas de entrega são realizadas?",
        "Qual é o prazo para solicitar reembolso de um produto avariado?",
        "Quando um pedido é considerado extraviado?",
        "Posso alterar o endereço depois que o pedido foi enviado?",
        "Como funciona a devolução por arrependimento?",
    ]

    for example in example_questions:

        if st.button(
            example,
            use_container_width=True,
        ):
            st.session_state.pending_question = example

    st.divider()

    if st.button(
        "🗑️ Limpar conversa",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.caption(
        "Projeto acadêmico desenvolvido para o "
        "Challenge Alura + Oracle."
    )


# ============================================================
# EXIBIÇÃO DO HISTÓRICO
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # Exibe fontes das respostas do agente
        if (
            message["role"] == "assistant"
            and message.get("sources")
        ):

            with st.expander("📚 Fontes utilizadas"):

                for source in message["sources"]:

                    st.markdown(
                        f"- `{source}`"
                    )


# ============================================================
# ENTRADA DO USUÁRIO
# ============================================================

prompt = st.chat_input(
    "Digite sua pergunta sobre a NexusFlow..."
)


# ============================================================
# PERGUNTA SELECIONADA NO MENU LATERAL
# ============================================================

if "pending_question" in st.session_state:

    prompt = st.session_state.pending_question

    del st.session_state.pending_question


# ============================================================
# PROCESSAMENTO DA PERGUNTA
# ============================================================

if prompt:

    # --------------------------------------------------------
    # Salva pergunta do usuário
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # --------------------------------------------------------
    # Resposta do agente
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "🔎 Consultando a base de conhecimento..."
        ):

            try:

                # Carrega o agente
                agent = get_rag_agent()

                # Mede tempo de resposta
                start_time = time.time()

                # Executa o RAG
                answer, sources = agent.answer_question(
                    prompt
                )

                # Calcula tempo
                elapsed_time = time.time() - start_time

                # ------------------------------------------------
                # Exibe resposta
                # ------------------------------------------------

                st.markdown(answer)

                # ------------------------------------------------
                # Exibe fontes
                # ------------------------------------------------

                if sources:

                    with st.expander(
                        "📚 Fontes utilizadas"
                    ):

                        for source in sources:

                            st.markdown(
                                f"- `{source}`"
                            )

                # ------------------------------------------------
                # Tempo de resposta
                # ------------------------------------------------

                st.caption(
                    f"⏱️ Tempo de resposta: "
                    f"{elapsed_time:.2f} segundos"
                )

                # ------------------------------------------------
                # Salva resposta no histórico
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )

            # ----------------------------------------------------
            # Tratamento de erros
            # ----------------------------------------------------

            except Exception as error:

                error_message = (
                    "Erro ao processar a pergunta: "
                    f"{error}"
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "sources": [],
                    }
                )