import { addArrowIcon, addBase, addCard, palette } from "./theme.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 4, "几何直观", "把单位球变成椭球", "SVD 的几何意义：Vᵀ 先换坐标，Σ 再沿正交方向拉伸，U 最后把结果旋转到输出空间。");

  addCard(slide, ctx, {
    x: 90, y: 216, w: 250, h: 286,
    title: "步骤 1: Vᵀ",
    body: "在输入空间中做正交变换。\n不改变长度，只改变观察坐标系。\n因此先把问题转到“最合适的方向基”中。",
    accent: palette.navy
  });
  await addArrowIcon(slide, ctx, 360, 338, 44, 44);
  addCard(slide, ctx, {
    x: 424, y: 216, w: 250, h: 286,
    title: "步骤 2: Σ",
    body: "沿各坐标轴独立缩放。\nσ₁,σ₂,... 表示拉伸强弱。\n小奇异值对应的信息容易被噪声淹没。",
    accent: palette.gold,
    fill: "#FFFDF6"
  });
  await addArrowIcon(slide, ctx, 694, 338, 44, 44);
  addCard(slide, ctx, {
    x: 758, y: 216, w: 250, h: 286,
    title: "步骤 3: U",
    body: "在输出空间做正交变换。\n把已经拉伸好的椭球转到最终方向。\n因此输出的主轴方向就是左奇异向量。",
    accent: palette.blue
  });

  ctx.addShape(slide, { x: 1038, y: 236, width: 124, height: 124, fill: "#F0F6FB", line: ctx.line("#C7D8E8", 2) });
  ctx.addText(slide, { text: "单位圆/\n单位球", x: 1062, y: 270, width: 76, height: 52, fontSize: 20, color: palette.ink, bold: true, align: "center" });
  ctx.addShape(slide, { x: 1046, y: 392, width: 112, height: 160, fill: "#FFF4D8", line: ctx.line("#E1B14F", 2) });
  ctx.addText(slide, { text: "椭球", x: 1072, y: 454, width: 62, height: 28, fontSize: 22, color: palette.ink, bold: true, align: "center" });

  ctx.addText(slide, {
    text: "结论：最大的奇异值给出最大放大倍数，最小奇异值衡量最弱方向；当某些奇异值非常小，矩阵就接近降秩。",
    x: 92, y: 586, width: 1088, height: 42, fontSize: 16, color: palette.slate
  });
  return slide;
}
