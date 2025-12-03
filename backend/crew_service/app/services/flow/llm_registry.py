from crewai import LLM

general_llm = LLM(
    model="openai/gpt-4.1-mini",
    # model="openai/gpt-4o-mini",
    temperature=0.7,
    # model="openai/gpt-5-mini",
    # model="openai/gpt-5-nano",
    # reasoning_effort="none",
    seed=42,
)

function_calling_llm = LLM(
    model="openai/gpt-4.1-mini",
    temperature=0.7,
    seed=42,
)