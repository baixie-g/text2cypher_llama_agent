from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


class LocalFewshotManager:
    def __init__(self, parquet_file: Optional[str] = "fewshot_examples.parquet"):
        """
        Initialize the LocalFewshotManager class by loading the parquet file.

        :param parquet_file: Path to the parquet file (relative to this module)
        """
        # Resolve the parquet file relative to this file's directory
        module_dir = Path(__file__).parent
        self.parquet_file_path = module_dir / parquet_file
        print(f"[DEBUG] fewshot_examples.parquet 路径: {self.parquet_file_path}")
        self.data_dict = self._load_parquet_to_dict(self.parquet_file_path)
        print(f"[DEBUG] fewshot_examples.parquet 加载完成，包含数据库: {list(self.data_dict.keys())}")

    def _load_parquet_to_dict(self, parquet_file: Path) -> Dict[str, List[str]]:
        """
        Load the parquet file and create a dictionary

        :return: A dictionary with databases as keys and lists of cypher queries as values
        """
        try:
            df = pd.read_parquet(parquet_file)
            print(f"[DEBUG] parquet文件内容预览: {df.head()}\n字段: {df.columns}")
        except Exception as e:
            print(f"[ERROR] 加载parquet文件失败: {e}")
            return {}
        data_dict = {}
        for database, examples in zip(
            df["database_reference_alias"], df["first_3_questions"]
        ):
            data_dict[database.split("_")[-1]] = examples
        return data_dict

    def get_fewshot_examples(self, question: Optional[str], database: str) -> List[str]:
        """
        Get few-shot examples for a specific database.

        :param database: The name of the database to retrieve examples for
        :return: A list of cypher queries for the specified database
        """
        print(f"[DEBUG] 查询fewshot，database: {database}")
        print(f"[DEBUG] 当前可用数据库: {list(self.data_dict.keys())}")
        examples = self.data_dict.get(database, [])
        print(f"[DEBUG] 返回fewshot数量: {len(examples)}")
        return examples

    def retrieve_fewshots(self, question, database, embed_model):
        """
        Get few-shot examples for a specific database.

        :param database: The name of the database to retrieve examples for
        :return: A list of cypher queries for the specified database
        """

        return self.data_dict.get(database, [])

    def store_fewshot_example(self, question, database, cypher, llm, embed_model, success = True):
        pass
