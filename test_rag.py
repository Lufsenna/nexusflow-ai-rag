from src.rag import NexusFlowRAG


def main():
    rag = NexusFlowRAG()

    testes = [
        "Qual é o status do pedido NF-1003?",
        "Como posso rastrear o pedido NF-1003?",
        "Como funciona a devolução por arrependimento?",
        "Qual é o prazo para solicitar reembolso de um produto avariado?",
        "Quando um pedido é considerado extraviado?",
        "Posso alterar o endereço depois que o pedido foi enviado?",
        "Quantas tentativas de entrega são realizadas?",
    ]

    print("\n" + "=" * 70)
    print("TESTES DO NEXUSFLOW RAG")
    print("=" * 70)

    for i, pergunta in enumerate(testes, 1):
        print(f"\n--- TESTE {i} ---")
        print(f"PERGUNTA: {pergunta}")

        try:
            resposta, fontes = rag.answer_question(pergunta)

            print(f"RESPOSTA: {resposta}")
            print(f"FONTES: {fontes}")

        except Exception as e:
            print(f"ERRO: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("TESTES FINALIZADOS")
    print("=" * 70)


if __name__ == "__main__":
    main()