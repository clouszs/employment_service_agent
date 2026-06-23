"""RAG 基础设施连通测试：embedding / LLM / Chroma 向量库。

用法：确保已设置 DASHSCOPE_API_KEY，然后 python selftest_rag_infra.py
"""

from app.core.config import settings

results: list[tuple[str, bool, str]] = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


print(f"配置: embedding={settings.embedding_model}({settings.embedding_dim}维)  llm={settings.llm_model}")
print(f"API key 已配置: {bool(settings.dashscope_api_key)}  base_url={settings.dashscope_base_url}\n")

# ---------- 1. Embedding ----------
try:
    from app.core.embedding import embed_query, embed_texts

    vecs = embed_texts(["应届毕业生落户需要哪些材料？", "三方协议怎么签订？"])
    ok = len(vecs) == 2 and len(vecs[0]) == settings.embedding_dim
    check("embedding 批量向量化", ok, f"条数={len(vecs)} 维度={len(vecs[0])}")
    qv = embed_query("档案怎么转递")
    check("embedding 单条查询", len(qv) == settings.embedding_dim, f"维度={len(qv)}")
except Exception as e:
    check("embedding 调用", False, f"异常: {e}")
    vecs = None

# ---------- 2. Chroma 向量库 ----------
try:
    from app.core import vectorstore as vs

    if vecs:
        vs.upsert(
            ids=["selftest_v1", "selftest_v2"],
            embeddings=vecs,
            documents=["应届毕业生申请落户需准备报到证、毕业证等材料。", "三方协议由毕业生、单位、学校三方签订。"],
            metadatas=[{"document_id": 9991, "chunk_id": 1}, {"document_id": 9992, "chunk_id": 2}],
        )
        check("Chroma 写入(upsert)", vs.count() >= 2, f"集合内向量数={vs.count()}")

        qv = vs.query(embed_query("落户要带什么证件"), top_k=2)
        top = qv[0] if qv else {}
        check(
            "Chroma 检索(query)",
            len(qv) >= 1 and top.get("metadata", {}).get("document_id") == 9991,
            f"命中top1 doc={top.get('metadata',{}).get('document_id')} score={top.get('score')}",
        )

        vs.delete(ids=["selftest_v1", "selftest_v2"])
        check("Chroma 删除(delete)", True, f"删除后向量数={vs.count()}")
except Exception as e:
    check("Chroma 操作", False, f"异常: {e}")

# ---------- 3. LLM ----------
try:
    from app.core.llm import chat, chat_stream

    ans = chat(
        [
            {"role": "system", "content": "你是就业指导助手，用一句话简洁回答。"},
            {"role": "user", "content": "三方协议是什么？"},
        ]
    )
    check("LLM 非流式对话", isinstance(ans, str) and len(ans) > 0, f"答案: {ans[:50]}...")

    chunks = list(chat_stream([{"role": "user", "content": "用5个字回答：你好吗"}]))
    streamed = "".join(chunks)
    check("LLM 流式对话", len(chunks) >= 1 and len(streamed) > 0, f"分片数={len(chunks)} 内容: {streamed[:30]}")
except Exception as e:
    check("LLM 调用", False, f"异常: {e}")

print("\n==== 汇总 ====")
passed = sum(1 for _, c, _ in results if c)
print(f"通过 {passed}/{len(results)}")
