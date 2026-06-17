import { addBase, addCard, palette } from "./theme.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 7, "典型应用", "SVD 在哪些问题里真正发挥作用？", "它既是理论分解工具，也是工程计算中的“万能中间层”。");

  addCard(slide, ctx, {
    x: 88, y: 214, w: 344, h: 320,
    title: "最小二乘与伪逆",
    body: "对超定方程 Ax≈b，SVD 给出 Moore-Penrose 伪逆：\nA⁺ = VΣ⁺Uᵀ。\n\n于是最小二乘解 x*=A⁺b 能自然处理秩亏和病态情况。",
    accent: palette.blue
  });
  addCard(slide, ctx, {
    x: 468, y: 214, w: 344, h: 320,
    title: "主成分分析 PCA",
    body: "对中心化数据矩阵 X 做 SVD，可直接得到主方向。\n右奇异向量对应主成分方向，奇异值平方反映方差贡献。",
    accent: palette.navy
  });
  addCard(slide, ctx, {
    x: 848, y: 214, w: 344, h: 320,
    title: "压缩与降噪",
    body: "保留前 k 个奇异值，丢弃小奇异值，既能减少存储，又能过滤弱噪声。\n图像压缩、推荐系统、语义检索都常用这类思想。",
    accent: palette.gold,
    fill: "#FFFDF6"
  });
  ctx.addText(slide, {
    text: "一句话概括：当问题里出现“主方向、低秩结构、病态求解、信息压缩”时，SVD 往往就是合适的工具。",
    x: 90, y: 584, width: 1086, height: 40, fontSize: 17, color: palette.slate
  });
  return slide;
}
