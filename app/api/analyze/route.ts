import { type NextRequest, NextResponse } from "next/server"

// Mock analysis function for demonstration
async function mockPoreAnalysis(imageBuffer: Buffer, magnification: number, maxDiamNm: number, threshMag: number) {
  // Simulate processing time
  await new Promise((resolve) => setTimeout(resolve, 2000))

  // Generate realistic mock data based on parameters
  const baseSize = 20 + (magnification / 100) * 10
  const histogram_data = []

  for (let i = 0; i < 80; i++) {
    const diameter = 5 + i * (maxDiamNm / 80)
    const pdf =
      Math.exp(-Math.pow((diameter - baseSize) / (baseSize * 0.4), 2)) * (0.6 + Math.random() * 0.8) * threshMag
    histogram_data.push({ diameter, pdf })
  }

  // Calculate statistics
  const totalPdf = histogram_data.reduce((sum, d) => sum + d.pdf, 0)
  const avgDiam = histogram_data.reduce((sum, d) => sum + d.diameter * d.pdf, 0) / totalPdf
  const maxPdfIndex = histogram_data.reduce((maxIdx, d, idx, arr) => (d.pdf > arr[maxIdx].pdf ? idx : maxIdx), 0)
  const modeDiam = histogram_data[maxPdfIndex].diameter

  return {
    avg_diam_nm: avgDiam,
    mode_diam_nm: modeDiam,
    histogram_data,
    output_dir: Date.now().toString(),
    pixel_size: 0.1 + Math.random() * 0.1,
    pore_fraction: 0.1 + Math.random() * 0.3,
    total_pores: Math.floor(500 + Math.random() * 1500),
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    const magnification = Number.parseInt(formData.get("magnification") as string)
    const maxDiamNm = Number.parseFloat(formData.get("max_diam_nm") as string)
    const threshMag = Number.parseFloat(formData.get("thresh_mag") as string)

    if (!file) {
      return NextResponse.json({ detail: "ファイルが提供されていません" }, { status: 400 })
    }

    // Convert file to buffer
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    console.log(`解析開始: ${file.name}, ${magnification}x, ${maxDiamNm}nm, ${threshMag}`)

    // Run mock analysis
    const result = await mockPoreAnalysis(buffer, magnification, maxDiamNm, threshMag)

    console.log("解析完了:", result.avg_diam_nm.toFixed(2), "nm")

    return NextResponse.json(result)
  } catch (error) {
    console.error("解析エラー:", error)
    return NextResponse.json(
      { detail: `解析に失敗しました: ${error instanceof Error ? error.message : "不明なエラー"}` },
      { status: 500 },
    )
  }
}
