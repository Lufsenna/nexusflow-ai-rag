# nexusflow-ai-rag

# 🚀 NexusFlow AI RAG

Sistema inteligente de atendimento e consulta de informações desenvolvido com **Retrieval-Augmented Generation (RAG)**.

O NexusFlow AI RAG combina uma base de conhecimento composta por documentos PDF, Markdown e dados operacionais em CSV com **Google Gemini**, permitindo responder perguntas utilizando informações recuperadas diretamente da base de dados.

O projeto foi desenvolvido com foco em **Inteligência Artificial, RAG, processamento de documentos, busca semântica e implantação em nuvem**.

---

## 📌 Sobre o projeto

O **NexusFlow AI RAG** é um agente inteligente capaz de consultar diferentes fontes de informação da plataforma NexusFlow e fornecer respostas contextualizadas.

O sistema trabalha com dois tipos principais de informação:

- 📚 Documentação e base de conhecimento;
- 📦 Dados operacionais de pedidos.

Entre as informações disponíveis estão:

- Status de pedidos;
- Rastreamento;
- Transportadora;
- Datas de envio e entrega;
- Prazos;
- Informações sobre devoluções;
- Reembolsos;
- Pedidos extraviados;
- Tentativas de entrega;
- Alteração de endereço;
- Planos e preços;
- Informações do produto;
- Políticas da plataforma.

---

# 🎯 Objetivo

O objetivo do projeto é desenvolver um assistente inteligente capaz de:

1. Receber uma pergunta do usuário;
2. Identificar o tipo de informação solicitada;
3. Consultar a fonte de dados adequada;
4. Recuperar os documentos ou registros relevantes;
5. Utilizar o contexto recuperado para gerar uma resposta;
6. Apresentar as fontes utilizadas na resposta.

---

# 🧠 Arquitetura RAG

O projeto utiliza o conceito de **Retrieval-Augmented Generation (RAG)**.

Fluxo simplificado:

```text
                 USUÁRIO
                    │
                    ▼
              Pergunta
                    │
                    ▼
             NexusFlow RAG
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
    Pedido específico     Pergunta geral
          │                   │
          ▼                   ▼
     pedidos.csv          Busca semântica
                              │
                              ▼
                         ChromaDB
                              │
                              ▼
                       Documentos
                              │
                              ▼
                         Contexto
                              │
                              ▼
                       Google Gemini
                              │
                              ▼
                          Resposta
                              │
                              ▼
                           Usuário