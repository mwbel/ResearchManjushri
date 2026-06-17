import { addBase, addCard, addFormulaBand, palette } from "./theme.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 5, "数值算法", "计算机如何稳定地求 SVD？", "工程实现通常不是“先求 AᵀA 再开根号”，而是采用更稳定的正交变换路线。");

  addFormulaBand(slide, ctx, "A  →  双对角化 B  →  对 B 做 QR/分治迭代  →  得到 U, Σ, V", 88, 208, 1104);

  addCard(slide, ctx, {
    x: 88, y: 312, w: 260, h: 232,
    title: "1. Householder 双对角化",
    body: "用一系列正交变换把一般矩阵约化为双对角矩阵 B。\n优点是数值稳定，且保留奇异值不变。",
    accent: palette.blue
  });
  addCard(slide, ctx, {
    x: 376, y: 312, w: 260, h: 232,
    title: "2. 迭代求奇异值",
    body: "对更小、更结构化的 B 做 QR 迭代或分治算法。\n这是 LAPACK、MATLAB、NumPy 等库的典型思路。",
    accent: palette.navy
  });
  addCard(slide, ctx, {
    x: 664, y: 312, w: 260, h: 232,
    title: "3. 回乘恢复奇异向量",
    body: "把累计的正交变换乘回去，得到左右奇异向量。\n需要时也可只求部分奇异值/奇异向量。",
    accent: palette.gold,
    fill: "#FFFDF6"
  });
  addCard(slide, ctx, {
    x: 952, y: 312, w: 240, h: 232,
    title: "为什么不直接算 AᵀA？",
    body: "因为条件数会平方，误差被放大。\n当矩阵病态时，直接特征分解会丢失精度。",
    accent: palette.red,
    fill: "#FFF7F6"
  });

  ctx.addText(slide, {
    text: "实践建议：大规模稀疏问题常用截断 SVD、Lanczos、随机 SVD；全量稠密问题则交给成熟线性代数库。",
    x: 90, y: 592, width: 1080, height: 38, fontSize: 16, color: palette.slate
  });
  return slide;
}
