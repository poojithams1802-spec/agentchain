def file_tool(filename):
    controlled_files = {
        "public.txt": "This is public sandbox information.",
        "config.txt": "Sandbox configuration information.",
        "notes.txt": "AgentChain controlled testing environment."
    }

    if filename not in controlled_files:
        return {
            "error": "File not found in sandbox."
        }

    return {
        "filename": filename,
        "content": controlled_files[filename]
    }