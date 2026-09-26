def search_tool(query):
    knowledge = {
        "python": "Python is a programming language.",
        "cybersecurity": "Cybersecurity protects systems, networks and data.",
        "agent": "An AI agent can observe, reason and perform actions."
    }

    result = knowledge.get(
        query.lower(),
        "No information found in controlled sandbox."
    )

    return {
        "query": query,
        "result": result
    }