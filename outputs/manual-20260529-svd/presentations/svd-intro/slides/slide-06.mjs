import { addBase, addCard, addFormulaBand, palette } from "./theme.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 6, "低秩近似", "截断 SVD 给出最优 rank-k 逼近", "保留最大的 k 个奇异值，就能在误差最小的意义下得到最佳低秩近似。");

  addFormulaBand(slide, ctx, "A_k = Σ(i=1→k) σᵢ uᵢ vᵢᵀ", 92, 208, 520);
  addCard(slide, ctx, {
    x: 88, y: 306, w: 520, h: 238,
    title: "Eckart-Young 定理",
    body: "在二范数或 Frobenius 范数下，所有 rank(A_k)=k 的矩阵里，截断 SVD 的 A_k 与原矩阵 A 的距离最小。\n\n这意味着：若只允许保留有限维信息，选最大的奇异值方向就是最优策略。",
    accent: palette.gold,
    fill: "#FFFDF6"
  });

  ctx.addShape(slide, { x: 672, y: 262, width: 450, height: 20, fill: "#EDF3F8" });
  const bars = [
    { x: 672, y: 262, w: 420, color: palette.navy, label: "σ₁" },
    { x: 672, y: 302, w: 316, color: palette.blue, label: "σ₂" },
    { x: 672, y: 342, w: 214, color: "#5D94BE", label: "σ₃" },
    { x: 672, y: 382, w: 118, color: "#8CB3CF", label: "σ₄" },
    { x: 672, y: 422, w: 54, color: "#BFD2E1", label: "σ₅" },
  ];
  for (const bar of bars) {
    ctx.addShape(slide, { x: bar.x, y: bar.y, width: bar.w, height: 24, fill: bar.color });
    ctx.addText(slide, { text: bar.label, x: 1128, y: bar.y + 2, width: 42, height: 18, fontSize: 15, color: palette.ink });
  }
  ctx.addText(slide, {
    text: "若只保留前 k=2 项，就抓住了绝大部分能量。\n这正是压缩、去噪和降维的理论基础。",
    x: 672, y: 476, width: 450, height: 54, fontSize: 17, color: palette.slate
  });
  return slide;
}
