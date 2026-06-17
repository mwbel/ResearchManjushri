import { addHeroTitle } from "./theme.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  addHeroTitle(
    slide,
    ctx,
    "奇异值分解 SVD\n及其在数值计算中的应用",
    "从矩阵结构、几何意义到稳定算法与典型应用，理解 SVD 为什么是数值线性代数中的基础工具。",
    "适用场景：最小二乘、降维、压缩、降噪、矩阵近似"
  );
  return slide;
}
