import os
import json
from typing import Any, Dict, Optional
import requests

from google.api_core import retry
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore, Schema
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.gemini import Gemini
from llama_index.llms.mistralai import MistralAI
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike
# 注意：避免在顶层导入 sentence_transformers 以减小对 PyTorch 的强依赖


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

        # 1) 优先从 Nacos 加载
        before = len(self.databases)
        try:
            self.load_databases_from_nacos()
        except Exception as ex:
            print(f"[WARN] 加载 Nacos 数据源失败: {ex}")
        after = len(self.databases)

        if after > before:
            print(f"-> 已从 Nacos 加载 {after - before} 个数据库，优先使用 Nacos 数据源，跳过本地默认配置和演示库。")
            print(f"Loaded {len(self.databases)} databases.")
            return

        # 2) 若 Nacos 未加载任何数据库，则回退到本地默认配置
        dft_database = os.getenv("NEO4J_DATABASE")
        if dft_database is not None:
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

        # 3) 继续尝试加载演示库（如果配置了）
        demo_databases = os.getenv("NEO4J_DEMO_DATABASES")
        if demo_databases is not None:
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

        print(f"Loaded {len(self.databases)} databases.")

    def load_databases_from_nacos(self, overrides: Optional[Dict[str, Any]] = None):
        """
        从 Nacos 拉取 dataId=qknow-datasources, group=DEFAULT_GROUP 的配置(JSON)，
        解析其中 type==2 的 Neo4j 数据源并注册为可用数据库。
        
        环境变量可配置：
        - NACOS_SERVER (默认 http://127.0.0.1:8848)
        - NACOS_DATA_ID (默认 qknow-datasources)
        - NACOS_GROUP (默认 DEFAULT_GROUP)
        - NACOS_NAMESPACE (可选)
        - NACOS_USERNAME / NACOS_PASSWORD (可选，开启鉴权时使用)
        - NEO4J_SCHEME (默认 bolt)
        """
        server = (overrides or {}).get("server", os.getenv("NACOS_SERVER", "http://127.0.0.1:8848"))
        data_id = (overrides or {}).get("data_id", os.getenv("NACOS_DATA_ID", "qknow-datasources"))
        group = (overrides or {}).get("group", os.getenv("NACOS_GROUP", "DEFAULT_GROUP"))
        namespace = (overrides or {}).get("namespace", os.getenv("NACOS_NAMESPACE", None))
        username = (overrides or {}).get("username", os.getenv("NACOS_USERNAME", None))
        password = (overrides or {}).get("password", os.getenv("NACOS_PASSWORD", None))
        preset_bearer_token = (overrides or {}).get("bearer_token", os.getenv("NACOS_BEARER_TOKEN", None))
        neo4j_scheme = os.getenv("NEO4J_SCHEME", "bolt")

        # 支持 Bearer Token 与 Basic Auth
        from requests.auth import HTTPBasicAuth
        auth_method = ((overrides or {}).get("auth_method") or os.getenv("NACOS_AUTH_METHOD", "auto")).lower()
        access_token: Optional[str] = None
        headers: Dict[str, str] = {}
        basic_auth: Optional[HTTPBasicAuth] = None
        login_cookies = None

        def _nacos_url(path: str) -> str:
            base = server.rstrip('/')
            if base.endswith('/nacos'):
                return f"{base}/{path.lstrip('/')}"
            return f"{base}/nacos/{path.lstrip('/')}"

        if preset_bearer_token:
            access_token = preset_bearer_token
            headers["Authorization"] = f"Bearer {access_token}"
            print("-> 使用预置的 NACOS_BEARER_TOKEN 访问配置")
        elif username and password:
            if auth_method in ("bearer", "auto"):
                # 依次尝试 v1/users/login 与 v1/login
                for login_url in [
                    _nacos_url("/v1/auth/users/login"),
                    _nacos_url("/v1/auth/login"),
                ]:
                    try:
                        print(f"-> 正在登录 Nacos(Bearer): {login_url} as {username}")
                        login_resp = requests.post(
                            login_url,
                            data={"username": username, "password": password},
                            timeout=10,
                        )
                        if login_resp.status_code == 200:
                            login_json = login_resp.json()
                            access_token = login_json.get("accessToken")
                            if access_token:
                                headers["Authorization"] = f"Bearer {access_token}"
                                login_cookies = login_resp.cookies
                                print("-> 成功获取 Nacos accessToken (并保存 Cookie)")
                                break
                        print(f"[WARN] Bearer 登录失败({login_resp.status_code}): {login_resp.text[:200]}")
                    except Exception as e:
                        print(f"[WARN] Nacos Bearer 登录异常: {e}")
                if auth_method == "bearer" and not access_token:
                    raise RuntimeError("Nacos Bearer 登录失败，且已禁止回退")

            if access_token is None and auth_method in ("basic", "auto"):
                basic_auth = HTTPBasicAuth(username, password)

        params: Dict[str, Any] = {"dataId": data_id, "group": group}
        if namespace:
            params["tenant"] = namespace
            params["namespaceId"] = namespace
        if access_token:
            # 有些环境需要 query 参数中的 accessToken，保险起见同时带上
            params["accessToken"] = access_token

        # 兼容 v1/v2 配置端点
        config_urls = [
            _nacos_url("/v1/cs/configs"),
            _nacos_url("/v2/cs/config"),
        ]

        last_error: Optional[str] = None
        cfg = None
        for url in config_urls:
            safe_params = {
                "dataId": params.get("dataId"),
                "group": params.get("group"),
                "tenant": params.get("tenant"),
                "namespaceId": params.get("namespaceId"),
                "accessToken": "***" if params.get("accessToken") else None,
            }
            auth_label = "basic" if basic_auth else ("bearer" if access_token else "none")
            print("-> 从 Nacos 拉取数据源:", url, "params=", json.dumps(safe_params, ensure_ascii=False), "auth=", auth_label)

            # 优先 Bearer / Basic
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                auth=basic_auth,
                cookies=login_cookies,
                timeout=10,
            )
            if resp.status_code == 200:
                try:
                    cfg = json.loads(resp.text)
                    break
                except Exception as e:
                    last_error = f"解析失败: {e}, 原始: {resp.text[:200]}"
            elif resp.status_code == 403:
                had_auth = bool(access_token or basic_auth)
                if not had_auth:
                    print("[WARN] 403 Forbidden，检测到未提供认证，尝试使用默认凭据 nacos/nacos...")
                    # 1) 先尝试 Bearer 登录（默认凭据）
                    try_default_user = os.getenv("NACOS_DEFAULT_USERNAME", "nacos")
                    try_default_pwd = os.getenv("NACOS_DEFAULT_PASSWORD", "nacos")
                    got_token = False
                    for login_url in [
                        _nacos_url("/v1/auth/users/login"),
                        _nacos_url("/v1/auth/login"),
                    ]:
                        try:
                            print(f"-> 尝试默认凭据 Bearer 登录: {login_url} as {try_default_user}")
                            login_resp = requests.post(
                                login_url,
                                data={"username": try_default_user, "password": try_default_pwd},
                                timeout=10,
                            )
                            if login_resp.status_code == 200:
                                login_json = login_resp.json()
                                access_token = login_json.get("accessToken")
                                if access_token:
                                    headers["Authorization"] = f"Bearer {access_token}"
                                    login_cookies = login_resp.cookies
                                    print("-> 默认凭据登录成功，使用 Bearer 重新请求配置")
                                    got_token = True
                                    break
                            print(f"[WARN] 默认凭据 Bearer 登录失败({login_resp.status_code}): {login_resp.text[:200]}")
                        except Exception as e:
                            print(f"[WARN] 默认凭据 Bearer 登录异常: {e}")

                    if got_token:
                        try:
                            resp2 = requests.get(
                                url,
                                params=params,
                                headers=headers,
                                cookies=login_cookies,
                                timeout=10,
                            )
                            if resp2.status_code == 200:
                                cfg = json.loads(resp2.text)
                                break
                            else:
                                last_error = f"Bearer 重新获取失败: {resp2.status_code} {resp2.text[:200]}"
                        except Exception as e:
                            last_error = f"Bearer 重新请求异常: {e}"

                    if cfg is None:
                        # 2) 回退 Basic 认证（默认凭据）
                        try:
                            print("-> 使用默认凭据 Basic 认证重新请求配置")
                            basic_auth = HTTPBasicAuth(try_default_user, try_default_pwd)
                            resp3 = requests.get(
                                url,
                                params=params,
                                auth=basic_auth,
                                timeout=10,
                            )
                            if resp3.status_code == 200:
                                cfg = json.loads(resp3.text)
                                break
                            else:
                                last_error = f"Basic 重新获取失败: {resp3.status_code} {resp3.text[:200]}"
                        except Exception as e:
                            last_error = f"Basic 重新请求异常: {e}"
                else:
                    print("[WARN] 403 Forbidden，已使用认证但仍被拒绝")
                    last_error = f"HTTP 403: {resp.text[:200]}"
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

        if cfg is None:
            raise RuntimeError(f"Nacos 请求失败: {last_error}")

        datasources = cfg.get("datasources", [])
        if not isinstance(datasources, list):
            raise ValueError("Nacos 配置字段 'datasources' 不是列表")

        loaded = 0
        for ds in datasources:
            try:
                # 仅处理 Neo4j
                if int(ds.get("type", 0)) != 2:
                    continue
                # 可选过滤：仅启用状态
                if ds.get("status") is not None and int(ds.get("status", 0)) != 1:
                    continue

                name = str(ds.get("name") or ds.get("databaseName") or "neo4j")
                host = str(ds.get("host") or "127.0.0.1")
                port = int(ds.get("port") or 7687)
                database_name = str(ds.get("databaseName") or "neo4j")
                user = str(ds.get("username") or "neo4j")
                pwd = str(ds.get("password") or "")
                ds_id_raw = ds.get("id")
                ds_id = str(ds_id_raw) if ds_id_raw is not None else None

                uri = f"{neo4j_scheme}://{host}:{port}"
                print(f"-> 注册 Nacos Neo4j 数据库: name={name}, uri={uri}, database={database_name}")

                graph_store = Neo4jPropertyGraphStore(
                    url=uri,
                    username=user,
                    password=pwd,
                    database=database_name,
                    enhanced_schema=True,
                    create_indexes=False,
                    timeout=30,
                )
                corrector_schema = self.get_corrector_schema(graph_store)

                # 使用 name 作为对外暴露的数据库名称键
                self.databases[name] = {
                    "graph_store": graph_store,
                    "corrector_schema": corrector_schema,
                    "name": name,
                    "id": ds_id,
                }
                loaded += 1
            except Exception as e:
                print(f"[WARN] 注册数据源失败: {ds}: {e}")
                continue

        print(f"-> 从 Nacos 加载 Neo4j 数据库数量: {loaded}")

    def init_embed_model(self):
        import os
        import ssl
        
        # 强制使用CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # 设置环境变量来解决SSL问题
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        os.environ['SSL_CERT_FILE'] = ''
        
        # 临时禁用SSL验证
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # 轻量降级：不强制安装 PyTorch/transformers，优先尝试 sentence_transformers，如失败则用随机向量
        try:
            from sentence_transformers import SentenceTransformer  # 延迟导入
            try:
                local_model_path = os.path.expanduser("~/.cache/huggingface/hub/models--BAAI--bge-m3")
                if os.path.exists(local_model_path):
                    print(f"使用本地缓存的模型: {local_model_path}")
                    self.embed_model = SentenceTransformer(local_model_path, device="cpu")
                else:
                    print("尝试从HuggingFace下载模型...")
                    self.embed_model = SentenceTransformer("BAAI/bge-m3", device="cpu")
            except Exception as e:
                print(f"无法加载BAAI/bge-m3模型: {e}")
                print("尝试使用备用模型 all-MiniLM-L6-v2 ...")
                self.embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                print("成功加载备用模型: all-MiniLM-L6-v2")
        except Exception as e2:
            print(f"sentence_transformers 不可用或加载失败: {e2}")
            print("使用简单的随机embedding作为最后备选...")
            
            class RandomEmbedding:
                def __init__(self, dimension=768):
                    self.dimension = dimension
                
                def encode(self, texts, **kwargs):
                    import numpy as np
                    if isinstance(texts, str):
                        texts = [texts]
                    return np.random.rand(len(texts), self.dimension).tolist()
            
            self.embed_model = RandomEmbedding()
            print("使用随机embedding作为临时解决方案")
        
        # 恢复SSL验证
        ssl._create_default_https_context = ssl.create_default_context


    def get_model_by_name(self, name):
        for model_name, model in self.llms:
            if model_name == name:
                return model
        return None

    def get_database_by_name(self, name: str):
        return self.databases[name]

    def get_database_name_by_id(self, database_id: str):
        for name, info in self.databases.items():
            if info.get("id") == database_id:
                return name
        return None

    def get_database_by_id(self, database_id: str):
        name = self.get_database_name_by_id(database_id)
        if name is not None:
            return self.databases.get(name)
        return None

    def get_corrector_schema(
        self, graph_store: Neo4jPropertyGraphStore
    ) -> list[Schema]:
        corrector_schema = [
            Schema(el["start"], el["type"], el["end"])
            for el in graph_store.get_schema().get("relationships")
        ]

        return corrector_schema
