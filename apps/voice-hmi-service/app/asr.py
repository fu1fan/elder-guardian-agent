def normalize_reply(text: str) -> tuple[str, str]:
    text = text.strip()
    if text in {"1", "我没事", "没事", "safe"}:
        return "safe", "我没事"
    if text in {"2", "需要帮助", "帮我", "help"}:
        return "help", "需要帮助"
    if text in {"3", "联系家属", "contact_family"}:
        return "contact_family", "联系家属"
    return text, text

