import ast
import re
import os
import logging

# ログ設定（初回のみ設定すればOK）
logging.basicConfig(
    level=logging.INFO,  # INFO, DEBUG などに切り替え可能
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # コンソールに出力
        logging.FileHandler("extract.log", encoding="utf-8")  # ファイルにも出力
    ]
)


def extract_definitions_from_file(file_path):
    ext = os.path.splitext(file_path)[1]

    if ext == ".py":
        return extract_python_definitions(file_path)
    elif ext in {".cpp", ".cc", ".cxx", ".hpp", ".h"}:
        return extract_cpp_definitions(file_path)
    else:
        print(f"[INFO] Unsupported file type: {file_path}")
        return []

def extract_python_definitions(file_path):
    logging.info(f"🔍 Processing Python file: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            tree = ast.parse(source)
    except Exception as e:
        logging.warning(f"[WARN] Failed to parse Python file {file_path}: {e}")
        return []

    items = []

    def visit(node, parents=[]):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            try:
                name = ".".join([p.name for p in parents] + [node.name])
                docstring = ast.get_docstring(node)
                source_code = ast.get_source_segment(source, node)

                items.append({
                    "name": name,
                    "type": type(node).__name__,
                    "docstring": docstring,
                    "source_code": source_code,
                    "file_path": file_path,
                    "language": "python",
                })

                logging.info(f"✅ Extracted {type(node).__name__}: {name}")
            except Exception as e:
                logging.warning(f"[WARN] Failed to process node {getattr(node, 'name', 'unknown')} in {file_path}: {e}")

        for child in ast.iter_child_nodes(node):
            visit(child, parents + [node] if isinstance(node, ast.ClassDef) else parents)

    visit(tree)
    logging.info(f"📄 {len(items)} definitions extracted from {file_path}")
    return items

# === C++用 ===
def extract_cpp_definitions(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except Exception as e:
        print(f"[WARN] Failed to read C++ file {file_path}: {e}")
        return []

    # C++関数・クラスの単純な正規表現
    func_pattern = re.compile(
        r"(?:\/\/[^\n]*\n|\/\*.*?\*\/\s*)*"  # preceding comments (optional)
        r"([a-zA-Z_][\w:<>]*)\s+"            # return type (e.g., void)
        r"([a-zA-Z_]\w*)\s*"                 # function name
        r"\(([^)]*)\)\s*"                    # arguments
        r"(\{(?:[^{}]*|\{[^}]*\})*\})?",     # optional body
        re.DOTALL
    )

    class_pattern = re.compile(
        r"(?:\/\/[^\n]*\n|\/\*.*?\*\/\s*)*"  # preceding comments
        r"class\s+([a-zA-Z_]\w*)\s*(?:[:\w\s,<>]*)?\{", re.MULTILINE
    )

    items = []

    # Extract class definitions
    for match in class_pattern.finditer(source):
        name = match.group(1)
        doc_comment = extract_preceding_comment(source, match.start())
        items.append({
            "name": name,
            "type": "ClassDef",
            "docstring": doc_comment,
            "source_code": match.group(0),
            "file_path": file_path,
            "language": "cpp",
        })

    # Extract function definitions
    for match in func_pattern.finditer(source):
        return_type, name, args, body = match.groups()
        doc_comment = extract_preceding_comment(source, match.start())

        items.append({
            "name": name,
            "type": "FunctionDef",
            "docstring": doc_comment,
            "source_code": match.group(0),
            "file_path": file_path,
            "language": "cpp",
        })

    return items

# 前のコメントを抽出する関数
def extract_preceding_comment(source, index):
    lines = source[:index].splitlines()
    comment_lines = []

    for line in reversed(lines):
        line = line.strip()
        if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            comment_lines.insert(0, line)
        elif line == "":
            continue
        else:
            break

    return "\n".join(comment_lines).strip() if comment_lines else None


from tqdm import tqdm
def extract_from_directory(directory):
    all_items = []
    supported_extensions = {".py", ".cpp", ".cc", ".cxx", ".hpp", ".h"}

    # 対象ファイルを一度すべてリストアップ
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in supported_extensions:
                path = os.path.join(root, file)
                file_list.append(path)

    # tqdmで進捗を表示しながら処理
    for path in tqdm(file_list, desc="Extracting definitions", unit="file"):
        all_items.extend(extract_definitions_from_file(path))

    return all_items