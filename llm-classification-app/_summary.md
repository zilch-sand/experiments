Leveraging Vertex AI, the LLM Classification App enables flexible text classification using industry-leading language models from Google, Anthropic, and Meta, with support for both single- and multi-label tasks. Its modular architecture separates business logic from the Streamlit frontend, facilitating backend deployment via FastAPI and robust unit testing. Notable features include prompt template customization, fuzzy matching of model outputs, token and cost estimation, model comparison (“Arena Mode”), and scalable batch processing. Pricing is dynamically sourced from [llm-prices](https://github.com/simonw/llm-prices), ensuring users receive up-to-date cost estimates. The backend's design enables easy integration with alternate frontends and workflow automation.

**Key findings/features:**
- Unified model interface via [litellm](https://github.com/BerriAI/litellm)
- Model output handling using rapidfuzz for fuzzy category matching
- Persistent batch state enables recovery and multi-batch submission in production workflows
- Judge models provide automated evaluation of classification quality
- Prompt review and RAG recommendations enhance classification accuracy and user experience
