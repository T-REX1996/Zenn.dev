from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 820
BG       = (240, 244, 255)
GKE_BG   = (225, 232, 255)
GKE_BD   = (90, 120, 210)
BOX_BG   = (255, 255, 255)
BOX_BD   = (100, 130, 220)
EXT_BG   = (220, 248, 230)
EXT_BD   = (50, 160, 90)
ARROW    = (70, 100, 200)
TEXT_W   = (30, 40, 80)
TEXT_DIM = (80, 95, 140)
LABEL    = (60, 80, 160)
PORT     = (30, 100, 210)
BADGE_BG = (180, 200, 255)

img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

def try_font(size):
    for name in ["C:/Windows/Fonts/msgothic.ttc",
                 "C:/Windows/Fonts/YuGothM.ttc",
                 "C:/Windows/Fonts/meiryo.ttc",
                 "/System/Library/Fonts/Helvetica.ttc"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()

f_title  = try_font(17)
f_body   = try_font(14)
f_small  = try_font(12)
f_port   = try_font(13)
f_badge  = try_font(11)

def rr(xy, r=10, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def text_c(txt, cx, y, font, fill):
    bb = draw.textbbox((0, 0), txt, font=font)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, y), txt, font=font, fill=fill)

def arrow(x1, y1, x2, y2, color=ARROW, w=2):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=w)
    # arrowhead
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 8
    for da in (2.5, -2.5):
        ax = x2 - size * math.cos(angle + da)
        ay = y2 - size * math.sin(angle + da)
        draw.line([(x2, y2), (int(ax), int(ay))], fill=color, width=w)

# ── GKE outer box ──────────────────────────────────────────
rr([30, 30, W - 30, 620], r=16, fill=GKE_BG, outline=GKE_BD, width=2)
draw.text((50, 44), "GKE Autopilot  /  namespace: kagent", font=f_body, fill=GKE_BD)

# ── ① kagent-ui ───────────────────────────────────────────
UI_X1, UI_Y1, UI_X2, UI_Y2 = 80, 90, 720, 195
rr([UI_X1, UI_Y1, UI_X2, UI_Y2], fill=BOX_BG, outline=BOX_BD, width=2)
# badge
rr([UI_X1 + 10, UI_Y1 + 10, UI_X1 + 28, UI_Y1 + 26], r=4, fill=BADGE_BG)
text_c("①", UI_X1 + 19, UI_Y1 + 11, f_badge, PORT)
draw.text((UI_X1 + 34, UI_Y1 + 11), "kagent-ui  (Next.js)", font=f_title, fill=TEXT_W)
draw.text((UI_X1 + 34, UI_Y1 + 34), "ブラウザからエージェントにチャットするUI", font=f_body, fill=TEXT_DIM)
draw.text((UI_X1 + 34, UI_Y1 + 54), "LoadBalancer で外部公開", font=f_body, fill=TEXT_DIM)
draw.text((UI_X2 - 75, UI_Y1 + 11), ":8080", font=f_port, fill=PORT)
# LB badge
rr([UI_X1 + 10, UI_Y1 + 75, UI_X1 + 130, UI_Y1 + 93], r=4, fill=(255, 240, 200), outline=(200, 140, 40), width=1)
text_c("LoadBalancer", UI_X1 + 70, UI_Y1 + 77, f_badge, (160, 100, 10))

# ── ② kagent-controller ───────────────────────────────────
CT_X1, CT_Y1, CT_X2, CT_Y2 = 80, 255, 720, 360
rr([CT_X1, CT_Y1, CT_X2, CT_Y2], fill=BOX_BG, outline=BOX_BD, width=2)
rr([CT_X1 + 10, CT_Y1 + 10, CT_X1 + 28, CT_Y1 + 26], r=4, fill=BADGE_BG)
text_c("②", CT_X1 + 19, CT_Y1 + 11, f_badge, PORT)
draw.text((CT_X1 + 34, CT_Y1 + 11), "kagent-controller  (Go)", font=f_title, fill=TEXT_W)
draw.text((CT_X1 + 34, CT_Y1 + 34), "エージェント管理のコア", font=f_body, fill=TEXT_DIM)
draw.text((CT_X1 + 34, CT_Y1 + 54), "CRD (Agent / ModelConfig) を監視し Pod を制御", font=f_body, fill=TEXT_DIM)
draw.text((CT_X2 - 75, CT_Y1 + 11), ":8083", font=f_port, fill=PORT)

# ── ③ kagent-postgresql ──────────────────────────────────
PG_X1, PG_Y1, PG_X2, PG_Y2 = 80, 420, 360, 540
rr([PG_X1, PG_Y1, PG_X2, PG_Y2], fill=BOX_BG, outline=BOX_BD, width=2)
rr([PG_X1 + 10, PG_Y1 + 10, PG_X1 + 28, PG_Y1 + 26], r=4, fill=BADGE_BG)
text_c("③", PG_X1 + 19, PG_Y1 + 11, f_badge, PORT)
draw.text((PG_X1 + 34, PG_Y1 + 11), "kagent-postgresql", font=f_title, fill=TEXT_W)
draw.text((PG_X1 + 14, PG_Y1 + 44), "セッション・チャット履歴の永続化", font=f_body, fill=TEXT_DIM)
draw.text((PG_X2 - 55, PG_Y1 + 11), ":5432", font=f_port, fill=PORT)

# ── ④ google-cloud-agent ─────────────────────────────────
AG_X1, AG_Y1, AG_X2, AG_Y2 = 400, 420, 720, 540
rr([AG_X1, AG_Y1, AG_X2, AG_Y2], fill=BOX_BG, outline=BOX_BD, width=2)
rr([AG_X1 + 10, AG_Y1 + 10, AG_X1 + 28, AG_Y1 + 26], r=4, fill=BADGE_BG)
text_c("④", AG_X1 + 19, AG_Y1 + 11, f_badge, PORT)
draw.text((AG_X1 + 34, AG_Y1 + 11), "google-cloud-agent  (Python)", font=f_title, fill=TEXT_W)
draw.text((AG_X1 + 14, AG_Y1 + 38), "エージェント本体", font=f_body, fill=TEXT_DIM)
draw.text((AG_X1 + 14, AG_Y1 + 57), "LLM 推論ループ / MCP ツール呼び出し", font=f_body, fill=TEXT_DIM)

# ── external: BigQuery MCP ────────────────────────────────
BQ_X1, BQ_Y1, BQ_X2, BQ_Y2 = 350, 660, 850, 720
rr([BQ_X1, BQ_Y1, BQ_X2, BQ_Y2], r=12, fill=EXT_BG, outline=EXT_BD, width=2)
text_c("bigquery.googleapis.com/mcp  (BigQuery MCP)", (BQ_X1 + BQ_X2) // 2, BQ_Y1 + 10, f_body, (20, 20, 20))
text_c("MCP (HTTPS)", (BQ_X1 + BQ_X2) // 2, BQ_Y1 + 30, f_small, (80, 80, 80))

# ── external: Vertex AI ───────────────────────────────────
VA_X1, VA_Y1, VA_X2, VA_Y2 = 350, 748, 850, 808
rr([VA_X1, VA_Y1, VA_X2, VA_Y2], r=12, fill=EXT_BG, outline=EXT_BD, width=2)
text_c("Vertex AI  Gemini 2.5 Flash", (VA_X1 + VA_X2) // 2, VA_Y1 + 10, f_body, (20, 20, 20))
text_c("LLM API", (VA_X1 + VA_X2) // 2, VA_Y1 + 30, f_small, (80, 80, 80))

# ── arrows ────────────────────────────────────────────────
UI_CX  = (UI_X1 + UI_X2) // 2
CT_CX  = (CT_X1 + CT_X2) // 2
PG_CX  = (PG_X1 + PG_X2) // 2
AG_CX  = (AG_X1 + AG_X2) // 2
BQ_CX  = (BQ_X1 + BQ_X2) // 2

# UI → controller
arrow(UI_CX, UI_Y2, CT_CX, CT_Y1)
text_c("API 呼び出し", UI_CX + 60, (UI_Y2 + CT_Y1) // 2 - 8, f_small, TEXT_DIM)

# controller → postgresql
arrow(PG_CX, CT_Y2, PG_CX, PG_Y1)

# controller → agent
arrow(AG_CX, CT_Y2, AG_CX, AG_Y1)

# agent → BigQuery MCP
arrow(AG_CX, AG_Y2, BQ_CX, BQ_Y1)
text_c("MCP (HTTPS)", AG_CX + 80, (AG_Y2 + BQ_Y1) // 2 - 8, f_small, TEXT_DIM)

# BigQuery → Vertex AI
arrow(BQ_CX, BQ_Y2, BQ_CX, VA_Y1)

# ── browser label (outside left) ─────────────────────────
draw.text((820, 130), "ブラウザ", font=f_body, fill=LABEL)
arrow(810, 142, UI_X2 + 2, 142, color=(160, 130, 30))

out = os.path.join(os.path.dirname(__file__), "component-diagram.png")
img.save(out, "PNG")
print(f"Saved: {out}  ({W}x{H})")
