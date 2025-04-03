import spacy
import os

# 加载模型，不禁用 NER
nlp = spacy.load('ja_ginza_bert_large', disable=["textcat"])

file_path = os.path.join(os.path.dirname(__file__), "春琴抄ルビ削除.txt")
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

MAX_BYTES = 40000
paragraphs = text.split('\n\n')

entities = []
current_block = ""
current_block_bytes = 0
offset = 0

# 只筛选这三个标签
target_labels = ["Person", "Province", "City"]

for paragraph in paragraphs:
    paragraph_bytes = len(paragraph.encode('utf-8'))
    if current_block_bytes + paragraph_bytes > MAX_BYTES:
        if current_block:
            doc = nlp(current_block)
            for ent in doc.ents:
                if ent.label_ in target_labels:
                    entities.append({
                        "text": ent.text,
                        "start": ent.start_char + offset - len(current_block),
                        "end": ent.end_char + offset - len(current_block),
                        "label": ent.label_
                    })
            offset += len(current_block)
            current_block = paragraph + "\n\n"
            current_block_bytes = paragraph_bytes + 2
        else:
            chunk_size = MAX_BYTES // 2
            for i in range(0, len(paragraph), chunk_size):
                chunk = paragraph[i:i+chunk_size]
                chunk_bytes = len(chunk.encode('utf-8'))
                if chunk_bytes <= MAX_BYTES:
                    doc = nlp(chunk)
                    for ent in doc.ents:
                        if ent.label_ in target_labels:
                            entities.append({
                                "text": ent.text,
                                "start": ent.start_char + offset,
                                "end": ent.end_char + offset,
                                "label": ent.label_
                            })
                    offset += len(chunk)
    else:
        current_block += paragraph + "\n\n"
        current_block_bytes += paragraph_bytes + 2

if current_block:
    doc = nlp(current_block)
    for ent in doc.ents:
        if ent.label_ in target_labels:
            entities.append({
                "text": ent.text,
                "start": ent.start_char + offset - len(current_block),
                "end": ent.end_char + offset - len(current_block),
                "label": ent.label_
            })

# 分开存储
persons = [e["text"] for e in entities if e["label"] == "Person"]
provinces = [e["text"] for e in entities if e["label"] == "Province"]
cities = [e["text"] for e in entities if e["label"] == "City"]

# 去重并排序
unique_persons = sorted(set(persons))
unique_provinces = sorted(set(provinces))
unique_cities = sorted(set(cities))

print(f"Person 标签共: {len(unique_persons)}")
print(f"Province 标签共: {len(unique_provinces)}")
print(f"City 标签共: {len(unique_cities)}")

with open("春琴抄_Person.txt", "w", encoding="utf-8") as f:
    for p in unique_persons:
        f.write(f"{p}\n")

with open("春琴抄_Province.txt", "w", encoding="utf-8") as f:
    for prov in unique_provinces:
        f.write(f"{prov}\n")

with open("春琴抄_City.txt", "w", encoding="utf-8") as f:
    for c in unique_cities:
        f.write(f"{c}\n")

# 也可选地将所有记录（含标签）写入同一个文件
with open("春琴抄_命名实体.txt", "w", encoding="utf-8") as f:
    for e in entities:
        f.write(f"{e['text']}\t{e['label']}\n")