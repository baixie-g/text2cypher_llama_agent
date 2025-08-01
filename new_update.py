# <id>: 4:98e5ef92-481a-4f67-9350-4b2605182e10:1412
# prevent: "避免感染分支杆菌病。"
# cure_way: "支气管肺泡灌洗"
# name: "肺泡蛋白质沉积症"
# cured_prob: "约40%"
# cause: "病因未明，推测与几方面因素有关：如大量粉尘吸入"
# cure_lasttime: "约3个月"
# cure_department: "内科,呼吸内科"
# easy_get: NaN
# desc: "肺泡蛋白质沉积症(简称PAP)，又称Rosen-Castle-man-Liebow综合征，是一种罕见疾病。"

# {
#   "id": "4:98e5ef92-481a-4f67-9350-4b2605182e10:1412",
#   "name": "肺泡蛋白质沉积症",
#   "type": "disease",
#   "aliases": [],
#   "definition": "肺泡蛋白质沉积症(简称PAP)，又称Rosen-Castle-man-Liebow综合征，是一种罕见疾病。",
#   "attributes": {
#     "prevent": ["避免感染分支杆菌病。"],
#     "cure_way": ["支气管肺泡灌洗"],
# "cured_prob": ["约40%"],
# "cause": ["病因未明，推测与几方面因素有关：如大量粉尘吸入"],


# "cure_lasttime": ["约3个月"],
# "cure_department": ["内科,呼吸内科"],
# "easy_get": [],
#   },
#   "source": "",
#   "create_time": ""
# }

# 实际上
# attributes.拉平了



from neo4j import GraphDatabase
import json

# Neo4j 连接信息
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "12345678"  # 修改为你自己的密码

# 实体标签和对应 type 字段值
ENTITY_TYPES = {
    "Disease": "disease",
    "Symptom": "symptom",
    "Drug": "drug",
    "Check": "check",
    "Department": "department",
    "Food": "food",
    "Producer": "producer",
    # 可以继续添加更多实体类型
}

# 初始化驱动
driver = GraphDatabase.driver(uri, auth=(username, password))

def wrap(val):
    """统一包装成数组，NaN 或 None 返回空数组"""
    if val is None or (isinstance(val, float) and str(val) == 'nan'):
        return []
    return [val]

def unify_entity_properties(tx, label, entity_type):
    # 查询原始数据（仅 Disease 有扩展字段，其他实体只查name/desc）
    if label == "Disease":
        query = f"""
        MATCH (e:{label})
        RETURN 
            e.id AS id,
            e.name AS name,
            e.desc AS description,
            e.prevent AS prevent,
            e.cure_way AS cure_way,
            e.cured_prob AS cured_prob,
            e.cause AS cause,
            e.cure_lasttime AS cure_lasttime,
            e.cure_department AS cure_department,
            e.easy_get AS easy_get,
            elementId(e) AS element_id
        """
    else:
        query = f"""
        MATCH (e:{label})
        RETURN 
            e.id AS id,
            e.name AS name,
            e.desc AS description,
            elementId(e) AS element_id
        """

    results = tx.run(query)

    for record in results:
        update_clauses = []
        update_clauses.append("SET e.type = $type")
        update_clauses.append("SET e.aliases = $aliases")
        update_clauses.append("SET e.definition = $definition")

        def add_update_clause(key, value):
            if value is not None:
                update_clauses.append(f"SET e.`attributes.{key}` = ${key}_attr")

        if label == "Disease":
            attributes = {
                "prevent": wrap(record["prevent"]),
                "cure_way": wrap(record["cure_way"]),
                "cured_prob": wrap(record["cured_prob"]),
                "cause": wrap(record["cause"]),
                "cure_lasttime": wrap(record["cure_lasttime"]),
                "cure_department": wrap(record["cure_department"]),
                "easy_get": [] if not record["easy_get"] or str(record["easy_get"]) == 'nan' else [record["easy_get"]]
            }
            for key, value in attributes.items():
                add_update_clause(key, value)
        # 非Disease实体不设置attributes相关字段

        delete_clauses = []
        if label == "Disease":
            delete_clauses = [
                "REMOVE e.desc",
                "REMOVE e.prevent",
                "REMOVE e.cure_way",
                "REMOVE e.cured_prob",
                "REMOVE e.cause",
                "REMOVE e.cure_lasttime",
                "REMOVE e.cure_department",
                "REMOVE e.easy_get"
            ]
        else:
            # 其他实体移除desc和所有attributes.*字段
            delete_clauses = ["REMOVE e.desc"]
            for key in ["prevent", "cure_way", "cured_prob", "cause", "cure_lasttime", "cure_department", "easy_get"]:
                delete_clauses.append(f"REMOVE e.`attributes.{key}`")

        full_query = f"""
        MATCH (e:{label}) WHERE elementId(e) = $element_id
        {' '.join(update_clauses)}
        {' '.join(delete_clauses)}
        """

        params = {
            "element_id": record["element_id"],
            "type": entity_type,
            "aliases": [],
            "definition": record["description"] or ""
        }

        if label == "Disease":
            for key, value in attributes.items():
                params[f"{key}_attr"] = value

        tx.run(full_query, params)
        print(f"[{label}] Updated: {record['name']}")

def main():
    with driver.session() as session:
        for label, entity_type in ENTITY_TYPES.items():
            print(f"\n🔄 Processing entities of type: {label}")
            session.execute_write(unify_entity_properties, label, entity_type)
    driver.close()
    print("✅ 所有实体已完成属性结构调整。")

if __name__ == "__main__":
    main()
