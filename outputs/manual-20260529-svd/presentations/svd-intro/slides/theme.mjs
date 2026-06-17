export const palette = {
  navy: "#123B64",
  blue: "#2F6E9E",
  gold: "#D7A23D",
  ink: "#1E293B",
  slate: "#5B6573",
  line: "#D8E2EC",
  soft: "#E9F1F7",
  soft2: "#F6F8FB",
  white: "#FFFFFF",
  green: "#2E8B57",
  red: "#C65B51",
};

export function addBase(slide, ctx, page, section, title, subtitle) {
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    width: ctx.W,
    height: ctx.H,
    fill: palette.white,
  });
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    width: ctx.W,
    height: 16,
    fill: palette.navy,
  });
  ctx.addText(slide, {
    text: section,
    x: 72,
    y: 42,
    width: 180,
    height: 24,
    fontSize: 18,
    color: palette.blue,
    bold: true,
  });
  ctx.addText(slide, {
    text: title,
    x: 72,
    y: 78,
    width: 860,
    height: 54,
    fontSize: 31,
    color: palette.ink,
    bold: true,
  });
  if (subtitle) {
    ctx.addText(slide, {
      text: subtitle,
      x: 72,
      y: 130,
      width: 920,
      height: 30,
      fontSize: 15,
      color: palette.slate,
    });
  }
  ctx.addShape(slide, {
    x: 72,
    y: 171,
    width: 1136,
    height: 1.5,
    fill: palette.line,
  });
  ctx.addText(slide, {
    text: "Numerical Linear Algebra",
    x: 72,
    y: 686,
    width: 260,
    height: 18,
    fontSize: 11,
    color: palette.slate,
  });
  ctx.addText(slide, {
    text: String(page).padStart(2, "0"),
    x: 1160,
    y: 682,
    width: 48,
    height: 18,
    fontSize: 12,
    color: palette.slate,
    align: "right",
  });
}

export function addHeroTitle(slide, ctx, title, subtitle, note) {
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    width: ctx.W,
    height: ctx.H,
    fill: palette.soft2,
  });
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    width: ctx.W,
    height: 24,
    fill: palette.navy,
  });
  ctx.addShape(slide, {
    x: 70,
    y: 98,
    width: 520,
    height: 470,
    fill: palette.white,
    line: ctx.line(palette.line, 1),
  });
  ctx.addShape(slide, {
    x: 640,
    y: 98,
    width: 570,
    height: 470,
    fill: "#F0F5FA",
    line: ctx.line("#C9D8E8", 1),
  });
  ctx.addText(slide, {
    text: "数值计算专题",
    x: 92,
    y: 124,
    width: 170,
    height: 24,
    fontSize: 18,
    color: palette.blue,
    bold: true,
  });
  ctx.addText(slide, {
    text: title,
    x: 92,
    y: 170,
    width: 430,
    height: 130,
    fontSize: 34,
    color: palette.ink,
    bold: true,
  });
  ctx.addText(slide, {
    text: subtitle,
    x: 92,
    y: 318,
    width: 430,
    height: 120,
    fontSize: 18,
    color: palette.slate,
  });
  ctx.addText(slide, {
    text: note,
    x: 92,
    y: 504,
    width: 430,
    height: 42,
    fontSize: 13,
    color: palette.slate,
  });
  drawMatrixPanel(slide, ctx, 690, 134);
  ctx.addText(slide, {
    text: "A = UΣVᵀ",
    x: 800,
    y: 474,
    width: 240,
    height: 48,
    fontSize: 30,
    color: palette.navy,
    bold: true,
    align: "center",
  });
}

export function addBulletList(slide, ctx, items, x, y, w, lineGap = 20, fontSize = 20) {
  let top = y;
  for (const item of items) {
    ctx.addShape(slide, {
      x,
      y: top + 8,
      width: 8,
      height: 8,
      fill: palette.gold,
    });
    ctx.addText(slide, {
      text: item,
      x: x + 20,
      y: top,
      width: w - 20,
      height: fontSize * 2.4,
      fontSize,
      color: palette.ink,
    });
    top += fontSize * 2.2 + lineGap;
  }
}

export function addCard(slide, ctx, { x, y, w, h, title, body, fill = palette.white, accent = palette.blue }) {
  ctx.addShape(slide, {
    x,
    y,
    width: w,
    height: h,
    fill,
    line: ctx.line(palette.line, 1),
  });
  ctx.addShape(slide, {
    x,
    y,
    width: 6,
    height: h,
    fill: accent,
  });
  ctx.addText(slide, {
    text: title,
    x: x + 22,
    y: y + 18,
    width: w - 36,
    height: 26,
    fontSize: 20,
    color: palette.ink,
    bold: true,
  });
  ctx.addText(slide, {
    text: body,
    x: x + 22,
    y: y + 56,
    width: w - 40,
    height: h - 70,
    fontSize: 16,
    color: palette.slate,
  });
}

export function addMatrixBlock(slide, ctx, { x, y, w, h, label, lines, accent = palette.blue, tone = palette.soft2 }) {
  ctx.addShape(slide, {
    x,
    y,
    width: w,
    height: h,
    fill: tone,
    line: ctx.line(palette.line, 1),
  });
  ctx.addText(slide, {
    text: label,
    x: x + 16,
    y: y + 12,
    width: w - 32,
    height: 24,
    fontSize: 18,
    color: accent,
    bold: true,
    align: "center",
  });
  ctx.addShape(slide, {
    x: x + 26,
    y: y + 46,
    width: 3,
    height: h - 72,
    fill: accent,
  });
  ctx.addShape(slide, {
    x: x + w - 29,
    y: y + 46,
    width: 3,
    height: h - 72,
    fill: accent,
  });
  ctx.addText(slide, {
    text: lines.join("\n"),
    x: x + 38,
    y: y + 54,
    width: w - 76,
    height: h - 82,
    fontSize: 20,
    color: palette.ink,
    face: ctx.fonts.mono,
    align: "center",
  });
}

export function addFormulaBand(slide, ctx, text, x, y, w) {
  ctx.addShape(slide, {
    x,
    y,
    width: w,
    height: 64,
    fill: "#EFF5FB",
    line: ctx.line("#C8D8E9", 1),
  });
  ctx.addText(slide, {
    text,
    x: x + 18,
    y: y + 14,
    width: w - 36,
    height: 36,
    fontSize: 26,
    color: palette.navy,
    bold: true,
    face: ctx.fonts.mono,
    align: "center",
  });
}

export async function addArrowIcon(slide, ctx, x, y, w = 34, h = 34, color = palette.blue) {
  return ctx.addLucideIcon(slide, { icon: "arrow-right", x, y, width: w, height: h, color });
}

function drawMatrixPanel(slide, ctx, x, y) {
  addMatrixBlock(slide, ctx, {
    x,
    y,
    w: 120,
    h: 220,
    label: "U",
    lines: ["u₁", "u₂", "⋮", "uₘ"],
    accent: palette.blue,
  });
  addMatrixBlock(slide, ctx, {
    x: x + 160,
    y,
    w: 120,
    h: 220,
    label: "Σ",
    lines: ["σ₁", "σ₂", "⋱", "σᵣ"],
    accent: palette.gold,
    tone: "#FFF8EA",
  });
  addMatrixBlock(slide, ctx, {
    x: x + 320,
    y,
    w: 150,
    h: 220,
    label: "Vᵀ",
    lines: ["v₁ᵀ", "v₂ᵀ", "⋮", "vₙᵀ"],
    accent: palette.navy,
  });
}
