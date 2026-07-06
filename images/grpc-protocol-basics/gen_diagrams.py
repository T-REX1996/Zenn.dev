import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.dirname(__file__)

BG        = (245, 247, 255)
BOX_BG    = (255, 255, 255)
BOX_BD    = (100, 130, 220)
OUTER_BG  = (228, 235, 255)
OUTER_BD  = (90, 120, 210)
ARROW     = (70, 100, 200)
ARROW_RES = (60, 170, 110)
TEXT_W    = (30, 40, 80)
TEXT_DIM  = (80, 95, 140)
LABEL     = (60, 80, 160)
PANEL_BD  = (150, 160, 200)


def try_font(size, bold=False):
    names = (
        ["C:/Windows/Fonts/YuGothB.ttc", "C:/Windows/Fonts/msgothic.ttc"]
        if bold
        else ["C:/Windows/Fonts/YuGothM.ttc", "C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/meiryo.ttc"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def rr(draw, xy, r=10, fill=None, outline=None, width=1, dash=False):
    if not dash:
        draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)
    else:
        draw.rounded_rectangle(xy, radius=r, fill=fill)
        x1, y1, x2, y2 = xy
        seg = 6
        gap = 5
        x = x1
        while x < x2:
            draw.line([(x, y1), (min(x + seg, x2), y1)], fill=outline, width=width)
            draw.line([(x, y2), (min(x + seg, x2), y2)], fill=outline, width=width)
            x += seg + gap
        y = y1
        while y < y2:
            draw.line([(x1, y), (x1, min(y + seg, y2))], fill=outline, width=width)
            draw.line([(x2, y), (x2, min(y + seg, y2))], fill=outline, width=width)
            y += seg + gap


def text_c(draw, txt, cx, y, font, fill):
    bb = draw.textbbox((0, 0), txt, font=font)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, y), txt, font=font, fill=fill)


def arrow(draw, x1, y1, x2, y2, color=ARROW, w=3, size=9):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=w)
    angle = math.atan2(y2 - y1, x2 - x1)
    for da in (2.5, -2.5):
        ax = x2 - size * math.cos(angle + da)
        ay = y2 - size * math.sin(angle + da)
        draw.line([(x2, y2), (int(ax), int(ay))], fill=color, width=w)


# ============================================================
# 図1: gRPCの全体アーキテクチャ
# ============================================================
def gen_architecture():
    W, H = 1200, 420
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = try_font(18, bold=True)
    f_body = try_font(15)
    f_small = try_font(13)

    # 左: クライアントプロセス（外枠）
    CX1, CY1, CX2, CY2 = 40, 60, 420, 360
    rr(d, [CX1, CY1, CX2, CY2], r=14, fill=OUTER_BG, outline=OUTER_BD, width=2)
    text_c(d, "クライアントプロセス", (CX1 + CX2) // 2, CY1 + 12, f_title, TEXT_W)

    # 内側: アプリケーションコード
    AX1, AY1, AX2, AY2 = CX1 + 30, CY1 + 55, CX2 - 30, CY1 + 130
    rr(d, [AX1, AY1, AX2, AY2], fill=BOX_BG, outline=BOX_BD, width=2)
    text_c(d, "アプリケーションコード", (AX1 + AX2) // 2, AY1 + 14, f_body, TEXT_W)
    text_c(d, 'stub.GetUser(request)', (AX1 + AX2) // 2, AY1 + 40, f_small, TEXT_DIM)

    arrow(d, (AX1 + AX2) // 2, AY2, (AX1 + AX2) // 2, 215)

    # 内側: Stub
    SX1, SY1, SX2, SY2 = CX1 + 30, 215, CX2 - 30, 295
    rr(d, [SX1, SY1, SX2, SY2], fill=BOX_BG, outline=BOX_BD, width=2)
    text_c(d, "Stub（自動生成コード）", (SX1 + SX2) // 2, SY1 + 14, f_body, TEXT_W)
    text_c(d, "リクエストをprotobufにシリアライズ", (SX1 + SX2) // 2, SY1 + 40, f_small, TEXT_DIM)

    # 右: gRPCサーバープロセス（外枠）
    SVX1, SVY1, SVX2, SVY2 = W - 420, 60, W - 40, 360
    rr(d, [SVX1, SVY1, SVX2, SVY2], r=14, fill=OUTER_BG, outline=OUTER_BD, width=2)
    text_c(d, "gRPCサーバープロセス", (SVX1 + SVX2) // 2, SVY1 + 12, f_title, TEXT_W)

    # 内側: gRPCランタイム
    RX1, RY1, RX2, RY2 = SVX1 + 30, SVY1 + 55, SVX2 - 30, SVY1 + 130
    rr(d, [RX1, RY1, RX2, RY2], fill=BOX_BG, outline=BOX_BD, width=2)
    text_c(d, "gRPCランタイム", (RX1 + RX2) // 2, RY1 + 14, f_body, TEXT_W)
    text_c(d, "受信データをprotobufからデシリアライズ", (RX1 + RX2) // 2, RY1 + 40, f_small, TEXT_DIM)

    arrow(d, (RX1 + RX2) // 2, RY2, (RX1 + RX2) // 2, 215)

    # 内側: Service実装
    IX1, IY1, IX2, IY2 = SVX1 + 30, 215, SVX2 - 30, 295
    rr(d, [IX1, IY1, IX2, IY2], fill=BOX_BG, outline=BOX_BD, width=2)
    text_c(d, "Service実装", (IX1 + IX2) // 2, IY1 + 14, f_body, TEXT_W)
    text_c(d, "(UserServiceServicer)", (IX1 + IX2) // 2, IY1 + 40, f_small, TEXT_DIM)

    # 中央: gRPC Channel（HTTP/2コネクション）
    MX1, MY1, MX2, MY2 = CX2 + 20, 220, SVX1 - 20, 290
    rr(d, [MX1, MY1, MX2, MY2], r=12, fill=(255, 255, 255), outline=(150, 100, 220), width=2, dash=True)

    req_y = 235
    res_y = 275

    text_c(d, "gRPC Channel（HTTP/2）", (MX1 + MX2) // 2, (req_y + res_y) // 2 - 9, f_small, (100, 60, 180))

    # Stub -> Channel -> Runtime（リクエスト、一直線）
    arrow(d, SX2, req_y, MX1, req_y, color=ARROW)
    arrow(d, MX2, req_y, RX1, req_y, color=ARROW)
    text_c(d, "GetUserRequest（protobuf）", (SX2 + RX1) // 2, MY1 - 26, f_small, TEXT_DIM)

    # Runtime -> Channel -> Stub（レスポンス、一直線）
    arrow(d, RX1, res_y, MX2, res_y, color=ARROW_RES)
    arrow(d, MX1, res_y, SX2, res_y, color=ARROW_RES)
    text_c(d, "User（応答・protobuf）", (SX2 + RX1) // 2, MY2 + 10, f_small, (40, 130, 85))

    d.rectangle([0, 0, W - 1, H - 1], outline=PANEL_BD, width=1)
    img.save(os.path.join(OUT_DIR, "architecture.png"), "PNG")
    print("saved architecture.png")


# ============================================================
# 図2: HTTP/1.1 と HTTP/2 の多重化の違い
# ============================================================
def gen_http_comparison():
    W, H = 1200, 520
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = try_font(20, bold=True)
    f_body = try_font(15)
    f_small = try_font(13)

    PX1, PY1, PX2, PY2 = 40, 60, 580, 470
    rr(d, [PX1, PY1, PX2, PY2], r=14, fill=OUTER_BG, outline=OUTER_BD, width=2)
    text_c(d, "HTTP/1.1（一本道）", (PX1 + PX2) // 2, PY1 + 16, f_title, TEXT_W)
    text_c(d, "コネクションを複数張って同時アクセスに対応", (PX1 + PX2) // 2, PY1 + 48, f_small, TEXT_DIM)

    lane_h = 90
    for i, label in enumerate(["Connection 1", "Connection 2", "Connection 3"]):
        ly1 = PY1 + 95 + i * (lane_h + 15)
        ly2 = ly1 + lane_h
        rr(d, [PX1 + 30, ly1, PX2 - 30, ly2], fill=BOX_BG, outline=BOX_BD, width=2)
        d.text((PX1 + 45, ly1 + 10), label, font=f_body, fill=TEXT_W)
        arrow(d, PX1 + 60, ly1 + 55, PX1 + 220, ly1 + 55)
        text_c(d, "req", PX1 + 140, ly1 + 32, f_small, TEXT_DIM)
        arrow(d, PX2 - 220, ly1 + 55, PX2 - 60, ly1 + 55, color=ARROW_RES)
        text_c(d, "res", PX2 - 140, ly1 + 32, f_small, (40, 130, 85))

    QX1, QY1, QX2, QY2 = 620, 60, 1160, 470
    rr(d, [QX1, QY1, QX2, QY2], r=14, fill=OUTER_BG, outline=OUTER_BD, width=2)
    text_c(d, "HTTP/2（多車線の高速道路）", (QX1 + QX2) // 2, QY1 + 16, f_title, TEXT_W)
    text_c(d, "1本のコネクションを複数ストリームで多重化", (QX1 + QX2) // 2, QY1 + 48, f_small, TEXT_DIM)

    OX1, OY1, OX2, OY2 = QX1 + 20, QY1 + 90, QX2 - 20, QY2 - 20
    rr(d, [OX1, OY1, OX2, OY2], r=12, fill=(255, 255, 255), outline=(150, 100, 220), width=2, dash=True)
    text_c(d, "1本のコネクション", (OX1 + OX2) // 2, OY1 + 8, f_body, (100, 60, 180))

    for i, label in enumerate(["Stream 1", "Stream 2", "Stream 3"]):
        ly1 = OY1 + 45 + i * (lane_h + 12)
        ly2 = ly1 + lane_h - 15
        rr(d, [OX1 + 25, ly1, OX2 - 25, ly2], fill=BOX_BG, outline=BOX_BD, width=2)
        d.text((OX1 + 40, ly1 + 8), label, font=f_body, fill=TEXT_W)
        arrow(d, OX1 + 55, ly1 + 45, OX1 + 220, ly1 + 45)
        arrow(d, OX2 - 220, ly1 + 45, OX2 - 55, ly1 + 45, color=ARROW_RES)

    d.rectangle([0, 0, W - 1, H - 1], outline=PANEL_BD, width=1)
    img.save(os.path.join(OUT_DIR, "http-comparison.png"), "PNG")
    print("saved http-comparison.png")


# ============================================================
# 図3: gRPCの4つの通信パターン
# ============================================================
def gen_streaming_patterns():
    W, H = 1200, 760
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = try_font(17, bold=True)
    f_sub = try_font(13)
    f_small = try_font(12)

    panels = [
        (40, 40, 590, 400, "① Unary RPC", "たとえるなら：自動販売機", "unary"),
        (610, 40, 1160, 400, "② Server streaming RPC", "たとえるなら：ラジオの実況中継", "server"),
        (40, 420, 590, 760, "③ Client streaming RPC", "たとえるなら：宅配便の集荷", "client"),
        (610, 420, 1160, 760, "④ Bidirectional streaming RPC", "たとえるなら：トランシーバーの会話", "bidi"),
    ]

    for px1, py1, px2, py2, title, subtitle, kind in panels:
        rr(d, [px1, py1, px2, py2], r=14, fill=OUTER_BG, outline=OUTER_BD, width=2)
        text_c(d, title, (px1 + px2) // 2, py1 + 14, f_title, TEXT_W)
        text_c(d, subtitle, (px1 + px2) // 2, py1 + 40, f_sub, TEXT_DIM)

        cx1, cx2 = px1 + 60, px2 - 220
        sx1, sx2 = px2 - 220, px2 - 60
        cy = (py1 + py2) // 2 + 30
        box_w, box_h = 140, 70

        rr(d, [cx1, cy - box_h // 2, cx1 + box_w, cy + box_h // 2], fill=BOX_BG, outline=BOX_BD, width=2)
        text_c(d, "クライアント", cx1 + box_w // 2, cy - 12, f_sub, TEXT_W)
        rr(d, [sx2 - box_w, cy - box_h // 2, sx2, cy + box_h // 2], fill=BOX_BG, outline=BOX_BD, width=2)
        text_c(d, "サーバー", sx2 - box_w // 2, cy - 12, f_sub, TEXT_W)

        ax1 = cx1 + box_w
        ax2 = sx2 - box_w

        if kind == "unary":
            arrow(d, ax1, cy - 18, ax2, cy - 18, color=ARROW)
            arrow(d, ax2, cy + 18, ax1, cy + 18, color=ARROW_RES)
        elif kind == "server":
            arrow(d, ax1, cy - 45, ax2, cy - 45, color=ARROW)
            text_c(d, "request", (ax1 + ax2) // 2, cy - 62, f_small, TEXT_DIM)
            for i, dy in enumerate([-5, 20, 45]):
                arrow(d, ax2, cy + dy, ax1, cy + dy, color=ARROW_RES)
            text_c(d, "response ×3", (ax1 + ax2) // 2, cy + 55, f_small, (40, 130, 85))
        elif kind == "client":
            for i, dy in enumerate([-45, -20, 5]):
                arrow(d, ax1, cy + dy, ax2, cy + dy, color=ARROW)
            text_c(d, "request ×3", (ax1 + ax2) // 2, cy - 62, f_small, TEXT_DIM)
            arrow(d, ax2, cy + 45, ax1, cy + 45, color=ARROW_RES)
            text_c(d, "response", (ax1 + ax2) // 2, cy + 55, f_small, (40, 130, 85))
        elif kind == "bidi":
            offsets = [(-45, ARROW), (-15, ARROW_RES), (15, ARROW), (45, ARROW_RES)]
            for dy, color in offsets:
                if color == ARROW:
                    arrow(d, ax1, cy + dy, ax2, cy + dy, color=color)
                else:
                    arrow(d, ax2, cy + dy, ax1, cy + dy, color=color)
            text_c(d, "双方向で自由なタイミング", (ax1 + ax2) // 2, cy + 62, f_small, TEXT_DIM)

    d.rectangle([0, 0, W - 1, H - 1], outline=PANEL_BD, width=1)
    img.save(os.path.join(OUT_DIR, "streaming-patterns.png"), "PNG")
    print("saved streaming-patterns.png")


if __name__ == "__main__":
    gen_architecture()
    gen_http_comparison()
    gen_streaming_patterns()
