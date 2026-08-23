import streamlit as st

from src.rag import NexusFlowRAG

st.set_page_config(
    page_title="NexusFlow AI",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 NexusFlow AI")
st.subheader("Assistente inteligente para políticas e operações logísticas")

st.info(
    "Faça perguntas sobre entregas, rastreamento, reembolsos, devoluções, "
    "cancelamentos e atendimento. As respostas são baseadas exclusivamente "
    "nos documentos internos cadastrados."
)


@st.cache_resource
def get_rag_agent():
    return NexusFlowRAG()


if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.header("Exemplos de perguntas")

    example_questions = [
        "Como posso rastrear um pedido?",
        "Quantas tentativas de entrega são realizadas?",
        "Qual é o prazo para solicitar reembolso de um produto avariado?",
        "Quando um pedido é considerado extraviado?",
        "Posso alterar o endereço depois que o pedido foi enviado?",
        "Como funciona a devolução por arrependimento?",
    ]

    for example in example_questions:
        if st.button(example, use_container_width=True):
            st.session_state.pending_question = example

    st.divider()

    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Projeto acadêmico desenvolvido para o Challenge Alura + Oracle.")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("📚 Fontes utilizadas"):
                for source in message["sources"]:
                    location = ""

                    if source.get("page"):
                        location = f" | Página: {source['page']}"

                    elif source.get("row"):
                        location = f" | Registro CSV: {source['row']}"

                    st.markdown(
                        f"- **{source['title']}**  \n"
                        f"Arquivo: `{source['source']}` "
                        f"| Categoria: {source['category']}"
                        f"{location}"
                    )


prompt = st.chat_input("Digite sua pergunta sobre a NexusFlow...")

if "pending_question" in st.session_state:
    prompt = st.session_state.pending_question
    del st.session_state.pending_question

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando a base de conhecimento..."):
            try:
                agent = get_rag_agent()
                result = agent.answer_question(prompt)

                st.markdown(result["answer"])

                if result["sources"]:
                    with st.expander("📚 Fontes utilizadas"):
                        for source in result["sources"]:
                            location = ""

                            if source.get("page"):
                                location = f" | Página: {source['page']}"

                            elif source.get("row"):
                                location = f" | Registro CSV: {source['row']}"

                            st.markdown(
                                f"- **{source['title']}**  \n"
                                f"Arquivo: `{source['source']}` "
                                f"| Categoria: {source['category']}"
                                f"{location}"
                            )

                st.caption(
                    f"Tempo de resposta: {result['elapsed_time']:.2f} segundos"
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"],
                    }
                )

            except Exception as error:
                error_message = f"Erro ao processar a pergunta: {error}"
                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "sources": [],
                    }
                )
