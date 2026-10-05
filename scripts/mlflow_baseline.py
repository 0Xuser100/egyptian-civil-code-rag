import mlflow


def main() -> None:
    mlflow.set_experiment("egyptian-civil-code-rag")

    with mlflow.start_run(run_name="baseline-rag"):

        mlflow.log_param("embedding_model", "BAAI/bge-m3")
        mlflow.log_param("llm_model", "qwen2.5:3b")
        mlflow.log_param("vector_store", "FAISS")
        mlflow.log_param("top_k", 5)
        mlflow.log_param("embedding_dimension", 1024)

        mlflow.log_metric("retrieval_recall_at_5", 1.00)
        mlflow.log_metric("citation_accuracy", 0.60)
        mlflow.log_metric("mean_answer_correctness_signal", 0.7417)
        mlflow.log_metric("abstention_accuracy", 0.80)
        mlflow.log_metric("unsupported_number_rate", 0.20)
        mlflow.log_metric("mean_latency_seconds", 23.34)

        print("Baseline logged successfully.")


if __name__ == "__main__":
    main()