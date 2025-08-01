import os

from google.api_core import retry
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore, Schema
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.gemini import Gemini
from llama_index.llms.mistralai import MistralAI
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike
from sentence_transformers import SentenceTransformer


class ResourceManager:
    def __init__(self):
        self.llms = []
        self.databases = {}
        self.embed_model = None
        self.init_llms()
        self.init_databases()
        self.init_embed_model()

    def init_llms(self):
        print("> Initializing all llms. This may take some time...")

        if os.getenv("OPENAI_API_KEY"):
            self.llms.extend(
                [
                    ("gpt-4o", OpenAI(model="gpt-4o", temperature=0)),
                ]
            )

        if os.getenv("GOOGLE_API_KEY"):
            google_retry = dict(
                retry=retry.Retry(initial=0.1, multiplier=2, timeout=61)
            )
            self.llms.extend(
                [
                    (
                        "gemini-1.5-pro",
                        Gemini(
                            model="models/gemini-1.5-pro",
                            temperature=0,
                            request_options=google_retry,
                        ),
                    ),
                    (
                        "gemini-1.5-flash",
                        Gemini(
                            model="models/gemini-1.5-flash",
                            temperature=0,
                            request_options=google_retry,
                        ),
                    ),
                ]
            )

        if os.getenv("ANTHROPIC_API_KEY"):
            self.llms.extend(
                [
                    (
                        "sonnet-3.5",
                        Anthropic(
                            model="claude-3-5-sonnet-latest",
                            max_tokens=8076,
                        ),
                    ),
                    (
                        "haiku-3.5",
                        Anthropic(
                            model="claude-3-5-haiku-latest",
                            max_tokens=8076,
                        ),
                    ),
                ]
            )

        if os.getenv("MISTRAL_API_KEY"):
            self.llms.extend(
                [
                    (
                        "mistral-medium",
                        MistralAI(
                            model="mistral-medium",
                            api_key=os.getenv("MISTRAL_API_KEY"),
                        ),
                    ),
                    (
                        "mistral-large",
                        MistralAI(
                            model="mistral-large-latest",
                            api_key=os.getenv("MISTRAL_API_KEY"),
                        ),
                    ),
                    (
                        "ministral-8b",
                        MistralAI(
                            model="ministral-8b-latest",
                            api_key=os.getenv("MISTRAL_API_KEY"),
                        ),
                    ),
                ]
            )

        if os.getenv("DEEPSEEK_API_KEY"):
            self.llms.extend(
                [
                    (
                        "deepseek-v3",
                        OpenAILike(
                            model="deepseek-chat",
                            api_base="https://api.deepseek.com/beta",
                            api_key=os.getenv("DEEPSEEK_API_KEY"),
                        ),
                    )
                ]
            )

        if os.getenv("ARK_API_KEY"):
            self.llms.extend(
                [
                    (
                        "ark-model",
                        OpenAILike(
                            model=os.getenv("ARK_MODEL_ID", "ep-20250716102319-wdqpt"),
                            api_base=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
                            api_key=os.getenv("ARK_API_KEY", "cb103329-5b77-418e-89f2-fea182318c91"),
                            api_version="2024-01-01",  # 添加 API 版本
                            is_chat_model=True,  # 关键修正
                        ),
                    ),
                    (
                        "doubao-seed-1.6",
                        OpenAILike(
                            model="doubao-seed-1-6-250615",
                            api_base=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
                            api_key=os.getenv("ARK_API_KEY", "cb103329-5b77-418e-89f2-fea182318c91"),
                            api_version="2024-01-01",
                            is_chat_model=True,
                        ),
                    )
                ]
            )

        print(f"Loaded {len(self.llms)} llms.")

    def init_databases(self):
        print("> Initializing all databases. This may take some time...")
        demo_databases = os.getenv("NEO4J_DEMO_DATABASES")

        if demo_databases != None:
            demo_databases = demo_databases.split(",")
            for db in demo_databases:
                print(f"-> Initializing demo database: {db}")
                try:
                    graph_store = Neo4jPropertyGraphStore(
                        url=os.getenv("NEO4J_URI"),
                        username=db,
                        password=db,
                        database=db,
                        enhanced_schema=True,
                        create_indexes=False,
                        timeout=30,
                    )
                    print(f"-> Getting corrector schema for {db} database.")
                    corrector_schema = self.get_corrector_schema(graph_store)

                    self.databases[db] = {
                        "graph_store": graph_store,
                        "corrector_schema": corrector_schema,
                        "name": db,
                    }
                except Exception as ex:
                    print(ex)

        dft_database = os.getenv("NEO4J_DATABASE")
        if dft_database != None:
            print(f"-> Initializing default database: {dft_database}")
            try:
                graph_store = Neo4jPropertyGraphStore(
                    url=os.getenv("NEO4J_URI"),
                    username=os.getenv("NEO4J_USERNAME"),
                    password=os.getenv("NEO4J_PASSWORD"),
                    database=os.getenv("NEO4J_DATABASE"),
                    enhanced_schema=True,
                    create_indexes=False,
                    timeout=30,
                )
                print(f"-> Getting corrector schema for {dft_database} database.")
                corrector_schema = self.get_corrector_schema(graph_store)
                print(f"-> 成功获取 corrector schema 为: {corrector_schema}")
                self.databases[dft_database] = {
                    "graph_store": graph_store,
                    "corrector_schema": corrector_schema,
                    "name": dft_database,
                }
            except Exception as ex:
                print(ex)

        print(f"Loaded {len(self.databases)} databases.")

    def init_embed_model(self):
        # # 如果模型已经下载到本地，请指定其路径；否则，直接用模型名从HuggingFace Hub下载
        # model_path = "/home/g0j/.cache/huggingface/hub/models--BAAI--bge-m3"  # 或者 "BAAI/bge-m3"

        # # 注意：这里要加上 trust_remote_code=True，如果模型需要额外的自定义代码支持
        # self.embed_model = HuggingFaceEmbedding(model_name=model_path, trust_remote_code=True)

        # # 如果 bge-m3 模型维度不是默认的768，你需要手动设置dimensions参数。
        # # 根据文档或模型详情确认正确的维度大小，这里假设为1536以匹配OpenAI的配置
        # self.embed_model.dimensions = 1536
        # model_path = "/home/g0j/.cache/huggingface/hub/models--BAAI--bge-m3"
        # self.embed_model = BgeEmbedding(model_path=model_path)
        import torch
        import os
        # 强制使用CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        self.embed_model = SentenceTransformer("BAAI/bge-m3", device="cpu")


    def get_model_by_name(self, name):
        for model_name, model in self.llms:
            if model_name == name:
                return model
        return None

    def get_database_by_name(self, name: str):
        return self.databases[name]

    def get_corrector_schema(
        self, graph_store: Neo4jPropertyGraphStore
    ) -> list[Schema]:
        corrector_schema = [
            Schema(el["start"], el["type"], el["end"])
            for el in graph_store.get_schema().get("relationships")
        ]

        return corrector_schema
