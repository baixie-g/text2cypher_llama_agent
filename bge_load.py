from transformers import AutoTokenizer, AutoModel

# HuggingFace 模型名称
model_name = "BAAI/bge-m3"

# 下载 tokenizer 和 model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# 本地保存路径（确保你有足够磁盘空间）
save_path = "/home/g0j/.cache/huggingface/hub/models--BAAI--bge-m3"

# 保存到本地
tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print(f"模型已保存至：{save_path}")