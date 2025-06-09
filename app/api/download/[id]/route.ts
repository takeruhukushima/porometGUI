import { type NextRequest, NextResponse } from "next/server"

type Params = {
  id: string
}

export async function GET(
  request: NextRequest,
  context: { params: { id: string } }
) {
  try {
    const { id } = context.params

    // Generate mock CSV data
    const csvContent = [
      "# Poromet 解析結果",
      "# 解析ID: " + id,
      "# 生成日時: " + new Date().toLocaleString("ja-JP"),
      "",
      "直径(nm),確率密度",
      // Generate some sample data
      ...Array.from({ length: 50 }, (_, i) => {
        const diameter = 10 + i * 2
        const pdf = Math.exp(-Math.pow((diameter - 30) / 15, 2)) * (0.8 + Math.random() * 0.4)
        return `${diameter.toFixed(1)},${pdf.toFixed(6)}`
      }),
      "",
      "# 統計情報",
      "# 平均直径: 28.5 nm",
      "# 最頻直径: 25.2 nm",
      "# 細孔率: 0.234",
      "# 検出細孔数: 1250",
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv; charset=utf-8" })

    return new NextResponse(blob, {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="poromet_results_${id}.csv"`,
      },
    })
  } catch (error) {
    console.error("ダウンロードエラー:", error)
    return NextResponse.json({ detail: "ダウンロードに失敗しました" }, { status: 500 })
  }
}
