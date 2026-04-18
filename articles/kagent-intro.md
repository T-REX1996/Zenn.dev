---
title: "Kagent入門 — KubernetesにAIエージェントを持ち込むOSSフレームワーク"
emoji: "🤖"
type: "tech"
topics: ["kubernetes", "ai", "kagent", "cncf", "devops"]
published: true
---

## Kagentとは

**Kagent**はKubernetes上でAIエージェントをネイティブに動かすためのOSSフレームワークです。Solo.ioが開発し、2025年5月にCNCFサンドボックスプロジェクトとして寄贈されました。

単なるチャットボットではなく、「考えて→ツールを呼び出して→結果を評価して→次の行動を決める」という**反復的な推論ループ**を持つのが特徴です。

| 項目 | 内容 |
|------|------|
| 初公開 | 2025年3月 |
| CNCF採択 | 2025年5月（Sandboxレベル） |
| GitHubスター | 1,000+（100日時点） |
| コントリビューター | 100名以上（85%以上がSolo.io外） |
| ライセンス | Apache 2.0 |

https://kagent.dev/

---

## なぜKubernetesにAIエージェントが必要なのか

Kubernetesの運用には多くのコンテキストスイッチが伴います。

- `kubectl` でPodの状態確認
- Prometheusでメトリクス確認
- ログ収集・分析
- ドキュメント参照

これらを人間が逐一こなすのは非効率です。AIエージェントがKubernetesのAPIやツールを直接呼び出せれば、**「なぜ？」という問いへの答えを自動的に探索**できます。

---

## Kagentを運用業務に活かす

Kagentは概念的なフレームワークにとどまらず、実際の運用シーンで具体的な価値を発揮します。

### 障害調査エージェントのデプロイ

障害発生時に人間が手動でログを追う代わりに、Kagentにエージェントをデプロイして自動調査させることができます。「なぜこのPodが落ちているのか」と問いかけると、エージェントがログ・イベント・リソース状態を横断的に調べてレポートを返してくれます。

```yaml
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata:
  name: incident-investigator
spec:
  description: "障害発生時にPodログ・イベントを自動調査するエージェント"
  tools:
    - name: pod-logs
    - name: kubectl
```

### インフラコストの自動調査

Prometheusやクラウドのメトリクスと連携することで、「どのNamespaceがリソースを過剰消費しているか」「未使用のリソースはどれか」を自然言語で問い合わせられます。定期的なコスト最適化レポートの自動生成にも応用できます。

```yaml
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata:
  name: cost-analyzer
spec:
  description: "インフラリソースのコストを自動調査するエージェント"
  modelConfig:
    provider: openai
    model: gpt-4o
  tools:
    - name: kubectl
    - name: prometheus
  systemPrompt: |
    あなたはKubernetesのコスト最適化エージェントです。
    以下の観点でリソース使用状況を調査し、レポートしてください。
    - Namespace別のCPU・メモリ使用率
    - リクエストに対して過剰にリソースを確保しているPod
    - 長期間稼働しているが利用されていない可能性があるリソース
```

---

## アーキテクチャ

Kagentは3つのレイヤーで構成されています。

```
 ユーザー（CLI / Dashboard）
        │  自然言語で指示
        ▼
┌─────────────────────────────────────────┐
│           Framework Layer               │
│  ・Kubernetes CRD でエージェントを宣言   │
│  ・Controller がデプロイ・管理           │
└───────────────────┬─────────────────────┘
                    │ エージェント起動
                    ▼
┌─────────────────────────────────────────┐
│            Agents Layer                 │
│  ・LLM による推論・計画                  │
│  ・タスクを複数ステップに分解            │
│  ・結果を評価して次のアクションを決定    │
└───────────────────┬─────────────────────┘
                    │ ツール呼び出し
                    ▼
┌─────────────────────────────────────────┐
│             Tools Layer                 │
│  ・kubectl   ・pod-logs                 │
│  ・Prometheus ・Helm ・Argo ・Istio     │
│  （MCP互換 / カスタムツール追加可能）    │
└─────────────────────────────────────────┘
                    │
                    ▼
         Kubernetes クラスター
```

### コア3コンポーネント

**1. Controller（Go製）**
Kubernetesのカスタムリソース定義（CRD）を管理するコントローラーです。`Agent` リソースを宣言するだけでエージェントがデプロイされます。

**2. Engine / App（ランタイム）**
エージェントの推論ループを実行するランタイムです。2種類から選べます。

| ランタイム | 特徴 |
|-----------|------|
| Python ADK | Google ADK / CrewAI / LangGraph連携、デフォルト |
| Go ADK | 起動約2秒（Pythonの約15秒と比較して高速）、低リソース消費 |

**3. CLI / Dashboard**
`kagent` CLIとWebダッシュボードでエージェントの管理・操作が可能です。

---

## カスタムリソース（CRD）

KagentはKubernetesのCRDを使って宣言的にエージェントを管理します。主なリソースは以下の3種類です。

### Agent
エージェント本体の定義です。使用するLLM・ツール・システムプロンプトを指定します。

```yaml
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata:
  name: my-agent
spec:
  modelConfig:
    provider: openai
    model: gpt-4o
  tools:
    - name: kubectl
    - name: pod-logs
  systemPrompt: "あなたはKubernetes運用の専門家です。"
```

### ModelConfig
LLMプロバイダーへの接続情報を定義します。APIキーはSecretで管理します。

```yaml
apiVersion: kagent.dev/v1alpha1
kind: ModelConfig
metadata:
  name: openai-config
spec:
  provider: openai
  model: gpt-4o
  apiKeySecret:
    name: openai-secret
    key: api-key
```

### Tool
エージェントが使用するカスタムツールを定義します。既存のMCPツールに加え、独自のツールを追加登録できます。

```yaml
apiVersion: kagent.dev/v1alpha1
kind: Tool
metadata:
  name: my-custom-tool
spec:
  description: "カスタムAPIを呼び出すツール"
  type: mcp
  mcp:
    server: my-mcp-server
    tool: call-api
```

これら3つのリソースを組み合わせることで、**インフラとしてエージェントを管理**できるのがKagentの大きな特徴です。

---

## 対応LLM

Kagentはベンダーロックインを避けるため、複数のLLMプロバイダーに対応しています。

- OpenAI
- Azure OpenAI
- Anthropic（Claude）
- Google Vertex AI
- Ollama（ローカルLLM）
- カスタムAIゲートウェイ

---

## 主なユースケース

### 1. トラブルシューティング支援
「このPodが落ちている原因を調べて」と自然言語で指示すると、ログ・イベント・リソース状態を自動で調査してレポートしてくれます。

### 2. クラスター状態の説明
「このDeploymentは何をしているのか」という問いに対し、マニフェストを解析して人間が読める形で説明します。

### 3. ランブック自動化
OOMKilledやCrashLoopBackOffなどの既知パターンを検出し、定義済みのワークフローに従って自動修復します。

### 4. パフォーマンス監視
Prometheusと連携してメトリクスを監視し、劣化を検知した際にアクションを起こします。

### 5. マニフェスト生成・デプロイ
要件をテキストで渡すとKubernetesマニフェストを生成し、そのままデプロイまで実行します。

---

## クイックスタート

### 前提条件

- kind（ローカルKubernetesクラスター）または既存のKubernetesクラスター
- 使用するLLMのAPIキー（例: OpenAI）

### インストール

```bash
# Kagent CLIをインストール後、クラスターにデプロイ
kagent install

# ダッシュボードを起動（ポートフォワードを自動設定）
kagent dashboard
```

### Agentリソースの例

```yaml
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata:
  name: k8s-troubleshooter
spec:
  description: "Kubernetesのトラブルシューティングを支援するエージェント"
  modelConfig:
    provider: openai
    model: gpt-4o
  tools:
    - name: pod-logs
    - name: kubectl
    - name: prometheus
```

`kubectl apply` するだけでエージェントが起動します。

---

## MCP（Model Context Protocol）との連携

KagentはMCP互換のツールをサポートしており、以下のCNCFプロジェクトと連携できます。

- **Argo** — ワークフロー管理
- **Helm** — パッケージ管理
- **Istio** — サービスメッシュ
- **Prometheus** — メトリクス監視

MCPによりツールのエコシステムが広がっており、カスタムツールの追加も容易です。

---

## まとめ

| ポイント | 内容 |
|---------|------|
| Kubernetes-native | CRDで宣言的にエージェントを管理 |
| マルチLLM対応 | OpenAI・Claude・Ollamaなど主要プロバイダーに対応 |
| MCP連携 | CNCF各プロジェクトのツールをそのまま活用 |
| CNCF Sandbox | ベンダーニュートラルなガバナンス |

Kagentはまだサンドボックスフェーズですが、コミュニティの成長速度は速く、Kubernetesの運用自動化において今後注目のプロジェクトです。実際に試してみたい方は公式のクイックスタートから始めてみてください。

---

## 参考リンク

- [Kagent 公式サイト](https://kagent.dev/)
- [GitHub — kagent-dev/kagent](https://github.com/kagent-dev/kagent)
- [CNCF プロジェクトページ](https://www.cncf.io/projects/kagent/)
- [CNCF Blog — Kagent: Bringing Agentic AI to Cloud Native](https://www.cncf.io/blog/2025/04/15/kagent-bringing-agentic-ai-to-cloud-native/)
- [Solo.io Blog — Contributing Kagent to CNCF](https://www.solo.io/blog/bringing-agentic-ai-to-kubernetes-contributing-kagent-to-cncf)
