import { addBase, addBulletList, addCard, palette } from "./theme.mjs";

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 9, "总结", "SVD 为什么值得掌握？", "它把线性代数结构、数值稳定算法和实际工程应用连接到了一起。");

  addBulletList(slide, ctx, [
    "理论上：SVD 为任意矩阵提供统一、完备的结构分解。",
    "几何上：它揭示了矩阵对空间的主方向拉伸与旋转规律。",
    "算法上：稳定 SVD 依赖正交变换与成熟迭代方法，避免病态放大。",
    "应用上：最小二乘、PCA、压缩、降噪、推荐系统都可从中受益。"
  ], 92, 214, 560, 8, 20);

  addCard(slide, ctx, {
    x: 720, y: 226, w: 446, h: 180,
    title: "一句话记忆",
    body: "SVD = 把复杂矩阵拆成最容易理解、最容易计算、也最容易压缩的形式。",
    accent: palette.gold,
    fill: "#FFFDF6"
  });
  addCard(slide, ctx, {
    x: 720, y: 434, w: 446, h: 120,
    title: "延伸方向",
    body: "可继续学习：伪逆、条件数、Lanczos/随机 SVD、PCA 与低秩矩阵恢复。",
    accent: palette.blue
  });
  ctx.addText(slide, {
    text: "谢谢聆听  |  Questions?",
    x: 72, y: 644, width: 1130, height: 30, fontSize: 24, color: palette.navy, bold: true, align: "center"
  });
  return slide;
}
