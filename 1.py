import pdfplumber
import os
import make_json
import re

# ===================== 配置区（你只改这里！）=====================
PDF_FILES = [
    "金融知识1.pdf",  # 改成你真实文件名
    "金融知识2.pdf"  # 改成你真实文件名
]
OUTPUT_TEXT = "finance_clean.txt"  # 清洗后文本
OUTPUT_JSON = "finance_finetune.json"  # 最终微调数据


# ===============================================================

# 1. 提取PDF文本
def extract_pdf_text(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        print(f"✅ 提取完成：{pdf_path}")
    except Exception as e:
        print(f"❌ 提取失败：{e}")
    return text


# 2. 清洗文本（去乱码、空格、目录、页码、短行）
def clean_text(text):
    text = re.sub(r'(\n\s*)+', '\n', text)
    text = re.sub(r'第.*?章|目录|页码|[\uf000-\uffff]', '', text)
    lines = text.split('\n')
    new_lines = [line.strip() for line in lines if len(line.strip()) > 10]
    return '\n'.join(new_lines)


# 3. 切块（200-400字一段，适合微调）
def split_chunks(text, chunk_size=350):
    chunks = []
    words = text.split()
    current = []
    count = 0
    for w in words:
        current.append(w)
        count += len(w) + 1
        if count >= chunk_size:
            chunks.append(' '.join(current))
            current = []
            count = 0
    if current:
        chunks.append(' '.join(current))
    return chunks


# 4. 生成微调格式（ instruction-input-output 标准）
def build_finetune_json(chunks):
    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "instruction": "请详细解释这段金融知识",
            "input": chunk,
            "output": chunk
        })
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 微调数据集已生成：{OUTPUT_JSON}")
    return data


# 主流程
if __name__ == "__main__":
    print("开始处理PDF → 微调数据集...")

    # 提取所有PDF
    all_text = ""
    for pdf in PDF_FILES:
        all_text += extract_pdf_text(pdf)

    # 清洗
    cleaned = clean_text(all_text)
    with open(OUTPUT_TEXT, 'w', encoding='utf-8') as f:
        f.write(cleaned)

    # 切块
    chunks = split_chunks(cleaned)

    # 生成JSON
    build_finetune_json(chunks)

    print("\n🎉 全部完成！")
    print("📄 清洗文本：", OUTPUT_TEXT)
    print("📄 微调用JSON：", OUTPUT_JSON)