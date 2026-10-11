# Matching engineering / Recall@5 evaluation

本輪完成快取正規化索引、接入 Streamlit、建立特質檢索 baseline 和可重跑評估。移除成功 API 呼叫後兩次各 1 秒的固定等待。

## Recall@5

50 位角色；200 個 query；seed=42。每位角色抽 3 個原有特質，產生 4 個 query。唯一 relevant label 是來源角色；每個隨機推薦不重複抽 5 位。

| 方法 | Recall@5 |
|---|---:|
| Random，一輪 | 9.5% |
| Random，1,000 輪平均 | 9.95% |
| Random，理論期望 | 10.0% |
| 精確特質 IDF baseline | 100.0% |
| 原有 dense 語意匹配 | 未量測：本機 Ollama 不可用 |

1,000 次 random 實驗的分數 95% 範圍是 6.0%–14.5%，這是重複實驗的分布範圍，不是模型品質的信賴區間。

## Query 特質數敏感度

| Query 特質數 | Recall@1 | Recall@5 |
|---|---:|---:|
| 1 | 59.5% | 94.0% |
| 2 | 94.5% | 100.0% |
| 3 | 100.0% | 100.0% |

這是**樂觀的來源角色找回代理測試**。Query 直接使用 catalog 特質，沒有自然語言改寫、否定偏好或人工 relevance judgement。其他角色可能也相關。100% 不能當成真實偏好匹配的準確率，也不能代表 dense 或 hybrid 有提升。

## 檢索延遲

比較上一輪的 uncached NumPy cosine 實作與本輪 prepared index；不是與 GitHub 原始 sklearn 實作的比較。使用真實 50×1024 corpus、2,000 個 seeded random query vector、20 次暖機、交替呼叫順序。

| 實作 | Median | P95 |
|---|---:|---:|
| 上一輪 uncached | 0.123 ms | 0.257 ms |
| 本輪 cached index | 0.057 ms | 0.144 ms |

Median 約 2.16 倍快；每次只省約 0.066 ms。所有 2,000 個 query 的 top-5 相同，分數通過 atol=1e-8 比對。一次 index 建立約 0.555 ms。

這個 corpus 很小，檢索本來就快；整體延遲仍主要受 Gemini 與 Ollama 影響。移除固定等待能少 2 秒，但尚未量測完整 API 路徑。沒有宣稱端到端 2 倍加速。

## 工程與重跑

- `retrieval.py`: corpus 正規化一次、獨立快照、只讀向量；query 驗證；穩定排序；精確特質 IDF baseline。
- `app.py`: 用 cache_resource 重用 prepared index。
- `evaluation.py`: Recall@5、seed、random sampling、逐 query 結果、catalog SHA-256、敏感度與延遲評估。
- `tests/test_retrieval.py`: 索引等價性、快照、特質排序、無匹配、Recall 分母及 random 不重複抽樣。

在專案執行 `python evaluation.py --seed 42 --output evaluation-results`。執行 `python -m unittest discover -s tests -v` 驗證；目前共 13 個測試通過。

下一個真正的品質驗證需要獨立 query、人工相關角色標註及同模型 query embedding，才能比較 dense-only / lexical-only / hybrid。現有 application 保留 dense 排序，沒有把未驗證的 hybrid 權重推入產品。
