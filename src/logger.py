import streamlit as st

from src.logger import registrar_interacao
from src.rag import responder_pergunta

st.set_page_config(
    page_title="NexusFlow AI RAG",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 NexusFlow AI RAG")
st.caption("Assistente baseado na base de conhecimento em PDF.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input("Digite sua pergunta sobre a NexusFlow...")

if pergunta:
    st.session_state.mensagens.append(
        {"role": "user", "content": pergunta}
    )

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando a base de conhecimento..."):
            try:
                resposta, fontes = responder_pergunta(pergunta)

                st.markdown(resposta)

                if fontes:
                    st.caption("**Fontes consultadas:** " + ", ".join(fontes))

                registrar_interacao(pergunta, resposta, fontes)

                st.session_state.mensagens.append(
                    {"role": "assistant", "content": resposta}
                )

            except Exception as erro:
                mensagem_erro = f"Erro: {erro}"
                st.error(mensagem_erro)

                st.session_state.mensagens.append(
                    {"role": "assistant", "content": mensagem_erro}
                )

with st.sidebar:
    st.header("Gerenciamento")

    st.info(
        "Caso você adicione ou altere PDFs em `data/documents`, "
        "execute novamente a ingestão."
    )

    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.rerun()
