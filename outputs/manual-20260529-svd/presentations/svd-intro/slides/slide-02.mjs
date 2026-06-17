import { addBase, addBulletList, addCard, palette } from "./theme.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 2, "问题背景", "为什么要研究 SVD？", "SVD 之所以重要，在于它能把任意矩阵拆成“旋转/反射 + 拉伸 + 旋转/反射”的标准结构。");

  addBulletList(slide, ctx, [
    "对任意实矩阵 A∈R^(m×n) 都存在，不要求方阵，也不要求可逆。",
    "能揭示矩阵的秩、主方向、能量分布和病态程度。",
    "在数值计算中比直接求特征分解更稳健，尤其适合非方阵与近奇异问题。"
  ], 86, 212, 530, 12, 20);

  addCard(slide, ctx, {
    x: 700, y: 214, w: 484, h: 122,
    title: "它回答了三个核心问题",
    body: "矩阵把空间中的向量“拉到哪里去”？\n哪些方向被放大最多？\n如果只保留最重要的信息，应该留下哪些分量？",
    fill: "#FBFCFE",
    accent: palette.gold
  });

  addCard(slide, ctx, {
    x: 80, y: 468, w: 335, h: 152,
    title: "数值稳定性",
    body: "SVD 是求伪逆和最小二乘问题的标准工具，面对病态矩阵时尤其可靠。",
    accent: palette.blue
  });
  addCard(slide, ctx, {
    x: 472, y: 468, w: 335, h: 152,
    title: "结构解释力",
    body: "奇异值大小反映矩阵作用强度，左右奇异向量刻画输入/输出空间的主方向。",
    accent: palette.navy
  });
  addCard(slide, ctx, {
    x: 864, y: 468, w: 335, h: 152,
    title: "应用范围广",
    body: "从图像压缩、推荐系统到 PCA 与数据降噪，几乎都能看到 SVD 的影子。",
    accent: palette.gold
  });
  return slide;
}
