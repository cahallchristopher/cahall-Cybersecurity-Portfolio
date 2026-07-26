#!/usr/bin/env python3
"""
CyberAI SOC Assistant
=====================

Document Loader

Scans cybersecurity knowledge base files,
extracts content,
creates metadata,
and prepares documents for RAG ingestion.
"""


from pathlib import Path
from datetime import datetime



# ==========================================================
# Supported Extensions
# ==========================================================

SUPPORTED_EXTENSIONS = {

    ".md",
    ".txt",
    ".py",
    ".sh",

    ".yaml",
    ".yml",

    ".conf",
    ".cfg",
    ".ini",

    ".html",

    ".json",

    ".toml",

    ".xml",

    ".csv",

    "",

}



# ==========================================================
# Ignore Directories
# ==========================================================

IGNORED_DIRECTORIES = {

    ".git",
    "__pycache__",

    "node_modules",

    "venv",
    ".venv",

    ".idea",
    ".vscode",

    "dist",
    "build",

}



# ==========================================================
# Ignore Files
# ==========================================================

IGNORED_FILES = {

    "package-lock.json",

    "data.schema.json",

}



# ==========================================================
# Security Domain Mapping
# ==========================================================

SECURITY_DOMAINS = {

    "sherlock":
        "OSINT",

    "maigret":
        "OSINT",

    "osint-framework":
        "OSINT",

    "recon":
        "Reconnaissance",

    "scanner":
        "Vulnerability Management",

    "scripts":
        "Security Automation",

    "fastapi":
        "Security Automation",

}



# ==========================================================
# Detect Document Type
# ==========================================================

def detect_document_type(path: Path):


    name = path.name.lower()

    suffix = path.suffix.lower()



    # Licenses

    if name.startswith("license"):

        return "license"



    # Configuration files

    if name in {

        "dockerfile",

        "makefile",

        "docker-compose.yml",

        "docker-compose.yaml",

    }:

        return "configuration"



    if suffix in {

        ".yaml",
        ".yml",

        ".toml",

        ".ini",

        ".conf",

        ".cfg",

    }:

        return "configuration"



    # Dependency files

    if name.endswith(

        (

            ".lock",

            ".sum",

        )

    ):

        return "dependency"



    # Source code

    if suffix in {

        ".py",

        ".sh",

    }:

        return "source_code"



    # Tests

    if (

        "test" in name

        or

        "tests" in path.parts

    ):

        return "test"



    # Documentation

    if suffix in {

        ".md",

        ".txt",

        ".html",

    }:

        return "documentation"



    return "other"





# ==========================================================
# Category Detection
# ==========================================================

def get_category(path: Path):


    categories = {

        "cves",

        "exploits",

        "payloads",

        "scripts",

        "tools",

    }



    for part in path.parts:


        if part in categories:

            return part



    return "general"





# ==========================================================
# Security Domain Detection
# ==========================================================

def get_security_domain(path: Path):


    path_string = str(path).lower()



    for keyword, domain in SECURITY_DOMAINS.items():


        if keyword in path_string:

            return domain



    return "General Security"





# ==========================================================
# Tool Detection
# ==========================================================

def get_tool_name(path: Path):


    parts = path.parts



    if "tools" in parts:


        index = parts.index("tools")



        if len(parts) > index + 1:

            return parts[index + 1]



    return None





# ==========================================================
# Read File
# ==========================================================

def read_file(path: Path):


    try:


        return path.read_text(

            encoding="utf-8",

            errors="ignore"

        )



    except Exception as error:


        print(
            f"[!] Failed reading {path}: {error}"
        )


        return None





# ==========================================================
# Scan Documents
# ==========================================================

def scan_documents(root_directory):


    documents = []



    root = Path(root_directory)



    print(
        f"[*] Scanning: {root}"
    )



    for file in root.rglob("*"):



        if not file.is_file():

            continue



        if any(

            ignored in file.parts

            for ignored in IGNORED_DIRECTORIES

        ):

            continue



        if file.name in IGNORED_FILES:

            continue



        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:

            continue




        content = read_file(file)



        if not content:

            continue




        metadata = {


            "source":
                str(file),


            "filename":
                file.name,


            "category":
                get_category(file),


            "security_domain":
                get_security_domain(file),


            "document_type":
                detect_document_type(file),


            "extension":
                file.suffix.lower(),


            "size":
                file.stat().st_size,


            "modified":
                datetime.fromtimestamp(

                    file.stat().st_mtime

                ).isoformat(),


        }



        tool = get_tool_name(file)



        if tool:

            metadata["tool"] = tool




        documents.append(

            {

                "content": content,

                "metadata": metadata,

            }

        )



    return documents





# ==========================================================
# Main Test
# ==========================================================

if __name__ == "__main__":



    docs = scan_documents(

        "data/documents/redteam-kb"

    )



    print()

    print("=" * 50)

    print(
        f"Documents loaded: {len(docs)}"
    )

    print("=" * 50)



    categories = {}

    domains = {}

    doc_types = {}



    for doc in docs:


        metadata = doc["metadata"]



        category = metadata["category"]

        domain = metadata["security_domain"]

        dtype = metadata["document_type"]



        categories[category] = (

            categories.get(category, 0) + 1

        )



        domains[domain] = (

            domains.get(domain, 0) + 1

        )



        doc_types[dtype] = (

            doc_types.get(dtype, 0) + 1

        )





    print("\nCategory Summary:")


    for key, value in categories.items():


        print(
            f"{key:20} : {value}"
        )




    print("\nSecurity Domain Summary:")


    for key, value in domains.items():


        print(
            f"{key:20} : {value}"
        )




    print("\nDocument Type Summary:")


    for key, value in doc_types.items():


        print(
            f"{key:20} : {value}"
        )
