---
title: "A2Aの仕組みを整理する — AIエージェント間通信プロトコルの基礎"
emoji: "🤝"
type: "tech"
topics: ["a2a", "llm", "agent", "googlecloud", "kagent"]
published: true
---

## はじめに

AIエージェントが実用段階に入り、複数のエージェントを組み合わせて使う場面が増えてきました。しかし現実には、エージェントはフレームワークごとに独自の設計を持っており、**異なるフレームワーク同士をそのまま繋ぐ標準的な手段がありませんでした。**

この問題に対して Google が 2025 年に提唱したのが **A2A（Agent-to-Agent）プロトコル**です。異なるフレームワークで作られたエージェント同士が、共通の仕様で通信できるようにすることを目的としたオープンなプロトコルです。

本記事では A2A の仕組みを、MCP やサブエージェントとの比較を交えながら整理します。

---

## KagentにA2Aを導入する設計イメージ

仕組みの説明に入る前に、「KagentというOSSに対してA2Aをどう導入するか」という設計の全体像を先に示しておきます。

https://kagent.dev/

現状の Kagent は、クラスター内のエージェント同士が Kubernetes の Service 経由で通信する構成です。外部フレームワークから呼び出すための標準インターフェースは持っていません。

```
【現状：Kagent クラスター内で閉じている】

外部エージェント
（LangGraph など）
        │
        │  ← 呼び出す手段がない
        ×
        │
GKE クラスター
├── SupervisorAgent（Kagent）
├── CostAnalyzerAgent（Kagent）
└── SecurityAgent（Kagent）
```

A2A を導入すると、Kagent エージェントを**外部から標準プロトコルで呼べるサービス**として公開できます。

```
【A2A導入後：外部エージェントから呼び出し可能】

外部エージェント
（LangGraph など）
        │
        │  ① GET /.well-known/agent.json  （能力の確認）
        │  ② POST /a2a  tasks/send        （タスクの委任）
        ▼
  ┌─────────────────────────────────────┐
  │  A2A サーバ層（新規追加）            │
  │  - Agent Card エンドポイント         │
  │  - tasks/send・tasks/get ルーティング│
  └──────────────┬──────────────────────┘
                 │ 内部呼び出し
                 ▼
  GKE クラスター（既存）
  ├── CostAnalyzerAgent（Kagent）
  └── SecurityAgent（Kagent）
```

設計の要点は **「A2A サーバ層を Kagent の前段に薄く追加する」** だけです。既存の Kagent エージェントのロジックはそのままに、外向きのインターフェースだけを A2A 仕様に合わせます。

具体的には次の 3 つを実装します。

| 実装するもの | 役割 |
|---|---|
| `/.well-known/agent.json` エンドポイント | 外部エージェントへの自己紹介（Agent Card） |
| `POST /a2a` エンドポイント | タスクの受け付けと Kagent への橋渡し |
| Kubernetes `Ingress` または `Service` | A2A サーバをクラスター外に公開 |

以降では、この設計を理解するために必要な A2A の仕組みを順番に説明します。

---

## A2Aが解決する問題

エージェント同士が通信しようとすると、今まで次の問題がありました。

```
フレームワークAのエージェント          フレームワークBのエージェント
┌──────────────────────┐              ┌──────────────────────┐
│ LangGraph Agent       │  ←──???──→  │ Kagent Agent          │
│                       │              │                       │
│  - 独自のAPIスキーマ  │              │  - 独自のAPIスキーマ  │
│  - 独自の認証方式     │              │  - 独自の認証方式     │
│  - 独自の状態管理     │              │  - 独自の状態管理     │
└──────────────────────┘              └──────────────────────┘
```

HTTP で繋ごうにも、どんなエンドポイントを叩けばいいか、認証はどうすればいいか、エラーはどう返ってくるか——全部フレームワークごとに違います。これを繋ぐために毎回カスタムのアダプターを書くのは現実的ではありません。

A2A は「エージェント同士の通信に使う共通の言葉」を定めたプロトコルです。

---

## MCPとの関係を整理する

A2A を理解する前に、先に登場した MCP との違いを整理します。混同しやすいポイントです。

```
          ツール呼び出し
          （データ・機能へのアクセス）
エージェント ─────────────────────→ MCP Server
               HTTP + JSON-RPC         │
                                       │
                                  ┌────┴────┐
                                  │  DB     │
                                  │  API    │
                                  │  CLI    │
                                  └─────────┘

          エージェント間の委任
          （タスクを別エージェントに任せる）
エージェントA ─────────────────────→ エージェントB
               HTTP + A2A プロトコル     │
                                        │
                                   （別フレームワーク・
                                     別チームが管理）
```

| | MCP | A2A |
|---|---|---|
| 接続先 | ツール・データソース | 別のエージェント |
| 返ってくるもの | ツール実行結果（データ） | タスクの完了・部分的な回答 |
| 状態 | ステートレス（1リクエスト完結） | ステートフル（タスクが続く） |
| 誰が作った | Anthropic | Google |

一言で言えば **MCP は「エージェントが道具を使う」、A2A は「エージェントが仕事を頼む」** です。

---

## 通信トランスポート：stdioとHTTPの違い

MCP と A2A はどちらも JSON-RPC をベースにしていますが、**通信経路（トランスポート）の選択肢が異なります**。

### stdio（標準入出力）

stdio トランスポートは、プロセスの標準入出力（stdin / stdout）を通じてメッセージをやり取りします。

```
エージェントプロセス
        │
        │ 子プロセスとして起動
        ▼
  MCP Server プロセス
  ┌──────────────────┐
  │  stdin  ←───────│←── リクエスト（JSON-RPC）
  │  stdout ────────→│──→ レスポンス（JSON-RPC）
  └──────────────────┘
  （同一マシン上で動作）
```

| 項目 | 内容 |
|------|------|
| 通信経路 | OS のパイプ（ネットワーク不要） |
| 認証 | 不要（同一プロセスツリー内） |
| 向いている用途 | ローカル CLI ツール・ファイルシステム操作 |
| 例 | `npx @modelcontextprotocol/server-filesystem` |

MCP の `npx` や `uvx` で起動する形式がこれです。Kagent の記事でローカル検証に使った構成がこれにあたります。

### HTTP（SSE）

HTTP トランスポートは、ネットワーク越しにメッセージをやり取りします。ストリーミングには **SSE（Server-Sent Events）** を使います。

```
エージェント                        MCP Server / A2A Agent
（別マシン・別Pod）                  （GKE上で稼働）
        │                                    │
        │── POST /rpc ──────────────────────>│  リクエスト（JSON-RPC）
        │<── 200 OK ─────────────────────────│  レスポンス
        │                                    │
        │── GET /sse ────────────────────────>│  ストリーミング開始
        │<── data: ... ───────────────────── │  イベント逐次配信
        │<── data: ... ──────────────────────│
```

| 項目 | 内容 |
|------|------|
| 通信経路 | HTTP/HTTPS（ネットワーク） |
| 認証 | Bearer トークン・API キーなど |
| 向いている用途 | リモートサービス・マイクロサービス間連携 |
| 例 | Kagent の BigQuery MCP（`RemoteMCPServer`） |

### どちらを使うか

```
接続先が同一マシン上のプロセス？
    │
    ├─ YES → stdio
    │         シンプルで設定が少ない
    │         ローカル開発・CLIツール向き
    │
    └─ NO  → HTTP（SSE）
              ネットワーク越しに複数クライアントが接続可能
              KubernetesのPod間・クラウドサービス向き
```

**A2A は HTTP 専用です。** 異なるフレームワークのエージェントがネットワーク越しに通信することを前提に設計されているため、stdio は選択肢にありません。

MCP は両方をサポートしており、ローカル開発では stdio・本番環境では HTTP という使い分けが一般的です。

```
MCP の使い分け
├── ローカル開発・CLIツール → stdio（npx / uvx で起動）
└── 本番・GKE上のPod間通信 → HTTP（RemoteMCPServer）

A2A
└── 常に HTTP（SSE）── リモートエージェント間通信のみ
```

---

## サブエージェントとA2Aの違い

「マルチエージェント構成」と聞いたとき、よく混同されるのが**ローカルサブエージェント**と **A2A（リモートエージェント）** です。Google の ADK（Agent Development Kit）ドキュメントでは、この 2 つを次のように区別しています。

> Local Sub-Agents are agents that run within the same application process as your main agent and are like internal modules or libraries, used to organize your code into logical, reusable components. Communication between a main agent and its local sub-agents is very fast because it happens directly in memory, without network overhead.
>
> Remote Agents (A2A) are independent agents that run as separate services, communicating over a network.
>
> — [Introduction to A2A - Agent Development Kit (ADK)](https://adk.dev/a2a/intro/)

図で整理するとこうなります。

```
【ローカルサブエージェント】

メインエージェント
（1プロセス）
├── サブエージェントA  ← メモリ直結・関数呼び出し同等
├── サブエージェントB  ← ネットワーク不要・低遅延
└── サブエージェントC  ← 同一フレームワーク内で完結

【A2A（リモートエージェント）】

メインエージェント
（別サービス・別マシン）
        │
        │ HTTP + A2A プロトコル
        ▼
リモートエージェントX  ← 独立したサービスとして稼働
（別チーム・別フレームワーク）
```

### どちらを使うか

ADK ドキュメントの指針を日本語にまとめると次のとおりです。

**ローカルサブエージェントが適しているケース**

- コードを論理的に分割して整理したいだけ
- 高頻度・低遅延の内部処理が必要
- 同じフレームワーク・同じデプロイ単位で完結する

**A2A が適しているケース**

- 別チームや別組織が保守するサービスと連携する
- 異なる言語・フレームワークで実装されたエージェントと繋ぐ
- コンポーネント間に**明示的な契約（API仕様）** を持たせたい
- マイクロサービスアーキテクチャとして独立してスケールさせたい

```
同じリポジトリ・同じチームが管理？
    │
    ├─ YES → ローカルサブエージェント
    │         コードの整理が目的
    │         関数呼び出しと同等のコスト
    │
    └─ NO  → A2A
              別サービス・別チーム・別言語
              ネットワーク越しの正式な契約として扱う
```

### Kagentの文脈で言うと

Kagent の `SupervisorAgent` が同じクラスター内の別 `Agent` を呼ぶのはローカルサブエージェントに近い構造です（Kubernetes の Service 経由ではありますが、同一フレームワーク・同一管理者が前提）。

これに対して、Kagent 外部の LangGraph エージェントや外部ベンダーのエージェントと繋ぐ場合に A2A が登場します。

```
Kagent 内部（ローカルサブエージェント相当）
SupervisorAgent
├── CostAnalyzerAgent  ← 同じ Kagent、同じ GKE クラスター
└── SecurityAgent      ← 同じ Kagent、同じ GKE クラスター

Kagent 外部との連携（A2A）
SupervisorAgent
        │ A2A プロトコル
        └──→ ApprovalAgent（社内 LangGraph サービス）
        └──→ VendorAgent（外部 SaaS）
```

---

## A2Aの4つの構成要素

A2A プロトコルは 4 つのコアコンセプトで成立しています。

### 1. Agent Card（エージェントの名刺）

A2A に対応したエージェントは、`/.well-known/agent.json` というエンドポイントに自分のプロフィールを公開します。

```
https://cost-analyzer.example.com/.well-known/agent.json
```

中身はこんな構造です。

```json
{
  "name": "CostAnalyzerAgent",
  "description": "KubernetesクラスターのGCPコストを分析するエージェント",
  "url": "https://cost-analyzer.example.com/a2a",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "analyze-namespace-cost",
      "name": "Namespace別コスト分析",
      "description": "Namespace別のCPU・メモリ使用率とGCP課金を集計する",
      "inputModes": ["text"],
      "outputModes": ["text", "data"]
    }
  ]
}
```

エージェントを呼び出したい側はまずここを見て、「このエージェントは何ができるか」を動的に把握します。

### 2. Task（タスク）

A2A における仕事の単位が **Task** です。「タスクを送る → エージェントが処理する → 結果が返る」が基本の流れです。

```
クライアント（呼び出す側）          エージェント（呼ばれる側）
      │                                    │
      │── POST /a2a ──────────────────────>│
      │   {                                │
      │     "method": "tasks/send",        │
      │     "params": {                    │
      │       "id": "task-001",            │
      │       "message": {                 │
      │         "role": "user",            │
      │         "parts": [{                │
      │           "text": "先月のNamespace │
      │                    別コストを出して"│
      │         }]                         │
      │       }                            │
      │     }                              │
      │   }                                │
      │                                    │ 処理中...
      │<── response ──────────────────────│
      │   {                                │
      │     "result": {                    │
      │       "id": "task-001",            │
      │       "status": { "state": "completed" },
      │       "artifacts": [...]           │
      │     }                              │
      │   }                                │
```

Task には `id` があり、ステートフルに追跡できます。長時間かかる処理でも、`tasks/get` で後から状態を確認できます。

### 3. Message と Part（メッセージの中身）

MCP のツール定義と似ていますが、A2A のメッセージは **マルチモーダルを前提にした Part の配列**で表現します。

```
Message
├── role: "user" | "agent"
└── parts: [
    Part（text）   → テキスト
    Part（file）   → ファイル（Base64 または URI）
    Part（data）   → 構造化データ（JSON）
]
```

テキストだけでなく、CSVやJSONの構造化データも 1 つのメッセージ内に混在させられます。

### 4. Artifact（成果物）

タスクの完了時にエージェントが返す成果物が **Artifact** です。

```json
{
  "artifacts": [
    {
      "name": "cost-report",
      "parts": [
        {
          "type": "text",
          "text": "## Namespace別コスト（先月）\n..."
        },
        {
          "type": "data",
          "data": {
            "namespaces": [
              { "name": "kagent", "cpu_cost": 12.4, "mem_cost": 8.1 }
            ]
          }
        }
      ]
    }
  ]
}
```

Artifact は複数返せます。テキストのレポートと生データを同時に返して、呼び出し元が必要な方を使う、という設計が可能です。

---

## A2Aの通信フロー全体

4 つの要素を組み合わせると、エージェント間の通信はこうなります。

```
スーパーバイザーエージェント（LangGraph）
        │
        │  ① Agent Card を取得
        │  GET /.well-known/agent.json
        ├──────────────────────────────→ CostAnalyzerAgent（Kagent）
        │<─────────────────────────────
        │  スキルを把握
        │
        │  ② タスクを送信
        │  POST /a2a  tasks/send
        ├──────────────────────────────→ CostAnalyzerAgent（Kagent）
        │                                       │
        │                               Gemini を呼び出して
        │                               kubectl / BQ にアクセス
        │                                       │
        │<─────────────────────────────
        │  Artifact（コスト集計結果）
        │
        │  ③ 結果を使って次の判断
        │  （コストが閾値超えなら承認エージェントへ委任）
        │
        │  POST /a2a  tasks/send
        ├──────────────────────────────→ ApprovalAgent（別フレームワーク）
        │<─────────────────────────────
        │  Artifact（承認・却下）
        │
        ▼
    最終回答をユーザーに返す
```

スーパーバイザーは Agent Card を読んでから仕事を委任するだけです。CostAnalyzerAgent が Kagent で動いているか LangGraph で動いているかは関係ありません。

---

## ストリーミング対応（Server-Sent Events）

Agent Card の `"streaming": true` を返したエージェントは、処理の途中経過をリアルタイムに返せます。

```
クライアント                                   エージェント
    │                                              │
    │── POST /a2a  tasks/sendSubscribe ──────────>│
    │                                              │ 処理開始...
    │<── data: {"status": "working"} ─────────────│
    │<── data: {"status": "working",               │  LLM推論中...
    │           "message": {"parts":               │
    │             [{"text": "kubectl実行中..."}]}} │
    │<── data: {"status": "completed",             │
    │           "artifacts": [...]} ──────────────│
    │                                              │
```

BQ クエリや kubectl の実行で数十秒かかる処理でも、「今どこまで進んでいるか」をクライアントにリアルタイム表示できます。

---

## Kagentとの関係

Kagent はマルチエージェント構成をネイティブにサポートしていますが、v0.x 時点では Kagent 同士のクラスター内通信が中心です。A2A を使うと、**Kagent エージェントを外部から標準プロトコルで呼べる**ようになります。

```
社内の別チームが作ったエージェント
（Python + LangGraph で実装）
        │
        │ A2A プロトコル
        ▼
Kagent で動いているエージェント
（GKE上、Gemini 2.5 Flash使用）
        │
        ├── kubectl MCP
        └── BigQuery MCP
```

Kagent 側から見れば、呼び出し元が社内エージェントであっても Claude Code であっても、受け取る HTTP リクエストは同じ形式になります。

---

## まとめ

| 項目 | 内容 |
|------|------|
| A2A の目的 | 異なるフレームワークのエージェント同士を繋ぐ共通プロトコル |
| MCP との違い | MCP はツール呼び出し、A2A はタスクの委任（エージェント→エージェント） |
| 発見の仕組み | Agent Card（`/.well-known/agent.json`）で能力を公開 |
| 仕事の単位 | Task（ステートフル・追跡可能） |
| 成果物 | Artifact（テキスト・構造化データ・ファイルを混在可） |
| ストリーミング | SSE で途中経過をリアルタイム配信 |

A2A の設計思想は「エージェントをマイクロサービスのように扱う」です。HTTP 上に乗り、Agent Card で自己記述し、標準のメッセージ形式で通信する——Web の世界でやってきたことをエージェント間通信に適用したプロトコルと理解できます。

---

## 参考リンク

- [A2A Protocol 公式サイト](https://google.github.io/A2A/)
- [GitHub — google/A2A](https://github.com/google/A2A)
- [Kagent公式サイト](https://kagent.dev/)
