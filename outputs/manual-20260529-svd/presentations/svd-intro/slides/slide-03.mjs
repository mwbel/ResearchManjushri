import { addArrowIcon, addBase, addFormulaBand, addMatrixBlock, palette } from "./theme.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, 3, "定义与定理", "SVD 的标准形式", "任何矩阵都可以写成左右正交基与非负对角缩放的乘积。");

  addFormulaBand(slide, ctx, "A = UΣVᵀ", 86, 208, 1108);

  addMatrixBlock(slide, ctx, {
    x: 108, y: 314, w: 220, h: 210,
    label: "U ∈ R^(m×m)",
    lines: ["UᵀU = I", "列向量为左奇异向量"],
    accent: palette.blue
  });
  await addArrowIcon(slide, ctx, 348, 402);
  addMatrixBlock(slide, ctx, {
    x: 402, y: 314, w: 220, h: 210,
    label: "Σ ∈ R^(m×n)",
    lines: ["σ₁ ≥ σ₂ ≥ ... ≥ σᵣ > 0", "其余元素为 0"],
    accent: palette.gold,
    tone: "#FFF8EA"
  });
  await addArrowIcon(slide, ctx, 642, 402);
  addMatrixBlock(slide, ctx, {
    x: 696, y: 314, w: 220, h: 210,
    label: "V ∈ R^(n×n)",
    lines: ["VᵀV = I", "列向量为右奇异向量"],
    accent: palette.navy
  });
  addMatrixBlock(slide, ctx, {
    x: 958, y: 314, w: 220, h: 210,
    label: "秩信息",
    lines: ["rank(A)=非零奇异值个数", "σ_min 体现接近奇异的程度"],
    accent: palette.green,
    tone: "#F3FBF6"
  });

  ctx.addText(slide, {
    text: "补充关系：AᵀA 的特征值为 σᵢ²，V 的列向量是 AᵀA 的特征向量；AAᵀ 的特征向量对应 U。",
    x: 92, y: 578, width: 1080, height: 42, fontSize: 16, color: palette.slate
  });
  return slide;
}
