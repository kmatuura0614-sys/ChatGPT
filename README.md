# GPT-6 Luna Decision Layer

GPT-6 Luna を使い、受信リクエストに対して次の3項目を一度に判定する Python パッケージです。

- コンテンツ分類
- 適切なハンドラーへのリクエストルーティング
- エージェントが直ちに実行すべき次アクション

Structured Outputs の JSON Schema で応答を固定し、Pydantic でアプリケーション境界でも検証します。

## セットアップ

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

API キーはコードへ書かず、環境変数に設定します。

```bash
# PowerShell
$env:OPENAI_API_KEY = "your_api_key_here"

# macOS/Linux
export OPENAI_API_KEY="your_api_key_here"
```

`.env.example` は変数名の例です。`.env` は Git の追跡対象外です。

## 使用例

```python
from decision_layer import DecisionLayer

layer = DecisionLayer()
decision = layer.decide(
    "本番環境へ最新バージョンをデプロイして",
    context={"environment": "production", "approval_required": True},
)

print(decision.category)
print(decision.route)
print(decision.next_action)
print(decision.risk, decision.confidence)
```

個別の値だけが必要な場合は、`classify_content`、`route_request`、`select_next_action` も利用できます。各メソッドは独立したモデル呼び出しを行うため、通常は `decide` を一度呼んで結果を再利用する方が効率的です。

モデルと reasoning effort は任意で環境変数から変更できます。

```text
OPENAI_DECISION_MODEL=gpt-6-luna
OPENAI_DECISION_REASONING_EFFORT=low
```

## テスト

```bash
pytest
```

テストは OpenAI クライアントをモックするため、API キーやネットワーク接続は不要です。
