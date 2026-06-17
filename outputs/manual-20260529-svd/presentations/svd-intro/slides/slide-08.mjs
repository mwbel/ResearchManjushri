import { addBase, addFormulaBand, addMatrixBlock, palette } from "./theme.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 8, "简单例子", "二维矩阵的低秩近似直觉", "通过一个 2×2 例子看“保留最大奇异值”意味着什么。");

  addMatrixBlock(slide, ctx, {
    x: 96, y: 238, w: 190, h: 178,
    label: "原矩阵 A",
    lines: ["3   1", "1   3"],
    accent: palette.navy
  });
  ctx.addText(slide, {
    text: "这个矩阵沿着 [1,1]ᵀ 与 [1,-1]ᵀ 两个正交方向作用强度不同。",
    x: 86, y: 444, width: 232, height: 72, fontSize: 17, color: palette.slate
  });

  addFormulaBand(slide, ctx, "奇异值：σ₁=4,  σ₂=2", 372, 246, 396);
  ctx.addText(slide, {
    text: "若只保留最大的 σ₁，对应 rank-1 近似：\nA₁ = 4·u₁v₁ᵀ",
    x: 404, y: 338, width: 332, height: 74, fontSize: 22, color: palette.ink, align: "center"
  });
  ctx.addText(slide, {
    text: "近似后的矩阵只保留“最主要的拉伸方向”，\n因此信息更少，但主结构被保留。",
    x: 390, y: 444, width: 360, height: 72, fontSize: 17, color: palette.slate, align: "center"
  });

  addMatrixBlock(slide, ctx, {
    x: 882, y: 238, w: 214, h: 178,
    label: "rank-1 近似 A₁",
    lines: ["2   2", "2   2"],
    accent: palette.gold,
    tone: "#FFF8EA"
  });
  ctx.addText(slide, {
    text: "虽然它不再等于 A，\n但在所有秩为 1 的矩阵中，A₁ 离 A 最近。",
    x: 848, y: 444, width: 280, height: 72, fontSize: 17, color: palette.slate, align: "center"
  });

  ctx.addText(slide, {
    text: "这就是截断 SVD 的核心思想：用更低的复杂度保留最关键的结构。",
    x: 90, y: 586, width: 1088, height: 34, fontSize: 17, color: palette.slate
  });
  return slide;
}
