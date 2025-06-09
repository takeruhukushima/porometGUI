"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, Download, BarChart3, Settings, ImageIcon, Server, AlertCircle, CheckCircle } from "lucide-react"

interface AnalysisParams {
  magnification: number
  max_diam_nm: number
  thresh_mag: number
}

interface AnalysisResult {
  avg_diam_nm: number
  mode_diam_nm: number
  histogram_data: Array<{ diameter: number; pdf: number }>
  output_dir: string
  pixel_size: number
  pore_fraction: number
  total_pores: number
  filtered_image?: string
  pore_map?: string
  histogram?: string
}

// Use environment variable or default to localhost
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

export default function PorometApp() {
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [params, setParams] = useState<AnalysisParams>({
    magnification: 300,
    max_diam_nm: 80,
    thresh_mag: 1.8,
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const checkApiStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`, {
        method: "GET",
        mode: "cors",
      })
      if (response.ok) {
        const data = await response.json()
        console.log("API Health:", data)
        setApiStatus("online")
      } else {
        setApiStatus("offline")
      }
    } catch (error) {
      console.log("API Health Check Failed:", error)
      setApiStatus("offline")
    }
  }

  useEffect(() => {
    checkApiStatus()
    const interval = setInterval(checkApiStatus, 10000) // Check every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setResult(null)
      setError(null)

      // Create image preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleParamChange = (key: keyof AnalysisParams, value: number) => {
    setParams((prev) => ({ ...prev, [key]: value }))
  }

  const runAnalysis = async () => {
    if (!selectedFile) {
      setError("画像ファイルを選択してください")
      return
    }

    if (apiStatus !== "online") {
      setError("バックエンドAPIが実行されていません。サーバーを起動してください。")
      return
    }

    setIsAnalyzing(true)
    setProgress(0)
    setError(null)

    try {
      console.log("実際の細孔解析を開始します...")

      const formData = new FormData()
      formData.append("file", selectedFile)
      formData.append("magnification", params.magnification.toString())
      formData.append("max_diam_nm", params.max_diam_nm.toString())
      formData.append("thresh_mag", params.thresh_mag.toString())

      // Progress simulation - slower for real analysis
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 3, 90))
      }, 1000)

      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        body: formData,
        mode: "cors",
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `解析に失敗しました: ${response.statusText}`

        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorMessage
        } catch {
          errorMessage = errorText || errorMessage
        }

        throw new Error(errorMessage)
      }

      const analysisResult = await response.json()
      setResult(analysisResult)
      console.log("実際の細孔解析が正常に完了しました:", analysisResult)
    } catch (err) {
      console.error("解析エラー:", err)
      setError(err instanceof Error ? err.message : "解析に失敗しました")
    } finally {
      setIsAnalyzing(false)
      setProgress(0)
    }
  }

  const downloadResults = async () => {
    if (!result) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/download/${result.output_dir}`, {
        mode: "cors",
      })
      if (!response.ok) throw new Error("ダウンロードに失敗しました")

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `poromet_results_${result.output_dir}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError("結果のダウンロードに失敗しました")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Poromet</h1>
          <p className="text-lg text-gray-600">実際の細孔サイズ分析ツール</p>
          <p className="text-sm text-gray-500">PoreSpy ライブラリを使用した本格的な解析</p>
        </div>

        {/* API Status Banner */}
        <div className="text-center mb-6">
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${
              apiStatus === "online"
                ? "bg-green-100 text-green-800"
                : apiStatus === "offline"
                  ? "bg-red-100 text-red-800"
                  : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {apiStatus === "online" ? (
              <CheckCircle className="h-4 w-4" />
            ) : apiStatus === "offline" ? (
              <AlertCircle className="h-4 w-4" />
            ) : (
              <Server className="h-4 w-4" />
            )}
            API ステータス: {apiStatus === "online" ? "準備完了" : apiStatus === "offline" ? "オフライン" : "確認中..."}
          </div>

          {apiStatus === "offline" && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg max-w-2xl mx-auto">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="text-left">
                  <h3 className="font-semibold text-red-800">バックエンドサーバーが実行されていません</h3>
                  <p className="text-sm text-red-700 mt-1">
                    実際の細孔解析を行うには、Pythonバックエンドサーバーを起動してください：
                  </p>
                  <code className="block bg-red-100 text-red-800 px-3 py-2 rounded mt-2 text-sm">
                    python backend/server.py
                  </code>
                  <p className="text-xs text-red-600 mt-2">サーバーは {API_BASE_URL} で起動します</p>
                  <p className="text-xs text-red-600 mt-1">
                    必要なライブラリ: porespy, fastapi, uvicorn, numpy, matplotlib, scikit-image
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Input Panel */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5" />
                  画像アップロード
                </CardTitle>
                <CardDescription>SEM画像を選択して実際の細孔サイズ解析を実行</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm text-gray-600">
                        {selectedFile ? selectedFile.name : "クリックして画像をアップロード"}
                      </p>
                    </label>
                  </div>
                  {selectedFile && (
                    <div className="text-sm text-green-600">✓ ファイル選択済み: {selectedFile.name}</div>
                  )}
                  {imagePreview && (
                    <div className="mt-4">
                      <img
                        src={imagePreview || "/placeholder.svg"}
                        alt="Preview"
                        className="w-full h-32 object-cover rounded-lg border"
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  解析パラメータ
                </CardTitle>
                <CardDescription>細孔解析の設定を調整</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="magnification">SEM倍率</Label>
                    <Input
                      id="magnification"
                      type="number"
                      value={params.magnification}
                      onChange={(e) => handleParamChange("magnification", Number(e.target.value))}
                      className="mt-1"
                    />
                    <p className="text-xs text-gray-500 mt-1">対応倍率: 10×, 20×, 50×, 100×, 200×, 300×</p>
                  </div>
                  <div>
                    <Label htmlFor="max_diam">最大直径 (nm)</Label>
                    <Input
                      id="max_diam"
                      type="number"
                      value={params.max_diam_nm}
                      onChange={(e) => handleParamChange("max_diam_nm", Number(e.target.value))}
                      className="mt-1"
                    />
                    <p className="text-xs text-gray-500 mt-1">解析する細孔の最大サイズ</p>
                  </div>
                  <div>
                    <Label htmlFor="thresh_mag">閾値補正倍率</Label>
                    <Input
                      id="thresh_mag"
                      type="number"
                      step="0.01"
                      value={params.thresh_mag}
                      onChange={(e) => handleParamChange("thresh_mag", Number(e.target.value))}
                      className="mt-1"
                    />
                    <p className="text-xs text-gray-500 mt-1">Otsu閾値の補正係数 (推奨: 1.8)</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Button
              onClick={runAnalysis}
              disabled={!selectedFile || isAnalyzing || apiStatus !== "online"}
              className="w-full"
              size="lg"
            >
              {isAnalyzing ? "実際の解析中..." : "細孔解析実行"}
            </Button>

            {isAnalyzing && (
              <div className="space-y-2">
                <Progress value={progress} className="w-full" />
                <p className="text-sm text-center text-gray-600">PoreSpyで画像を解析中... {progress}%</p>
                <p className="text-xs text-center text-gray-500">実際の解析には時間がかかります</p>
              </div>
            )}
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {result && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    実際の解析結果
                  </CardTitle>
                  <CardDescription>PoreSpyによる細孔サイズ分布解析が完了しました</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="summary" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="summary">サマリー</TabsTrigger>
                      <TabsTrigger value="distribution">分布</TabsTrigger>
                      <TabsTrigger value="details">詳細</TabsTrigger>
                    </TabsList>

                    <TabsContent value="summary" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                          <h3 className="font-semibold text-blue-900">平均直径</h3>
                          <p className="text-2xl font-bold text-blue-700">{result.avg_diam_nm.toFixed(2)} nm</p>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                          <h3 className="font-semibold text-green-900">最頻直径</h3>
                          <p className="text-2xl font-bold text-green-700">{result.mode_diam_nm.toFixed(2)} nm</p>
                        </div>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="font-semibold text-gray-900">ピクセルサイズ</h3>
                        <p className="text-lg text-gray-700">{result.pixel_size.toFixed(4)} nm/px</p>
                      </div>
                    </TabsContent>

                    <TabsContent value="distribution" className="space-y-4">
                      {/* ヒストグラム画像 */}
                      <div className="bg-white p-4 rounded-lg border border-gray-200">
                        <h4 className="font-semibold mb-2">細孔サイズ分布ヒストグラム</h4>
                        {result.histogram ? (
                          <img 
                            src={`data:image/png;base64,${result.histogram}`} 
                            alt="細孔サイズ分布"
                            className="w-full h-auto rounded"
                          />
                        ) : (
                          <div className="h-60 flex items-center justify-center bg-gray-50 rounded">
                            <p className="text-gray-500">ヒストグラムが利用できません</p>
                          </div>
                        )}
                      </div>

                      {/* フィルター画像と細孔マップ */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                          <h4 className="font-semibold mb-2">フィルター画像</h4>
                          {result.filtered_image ? (
                            <img 
                              src={`data:image/png;base64,${result.filtered_image}`} 
                              alt="フィルター画像"
                              className="w-full h-auto rounded"
                            />
                          ) : (
                            <div className="h-48 flex items-center justify-center bg-gray-50 rounded">
                              <p className="text-gray-500">画像が利用できません</p>
                            </div>
                          )}
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                          <h4 className="font-semibold mb-2">細孔マップ</h4>
                          {result.pore_map ? (
                            <img 
                              src={`data:image/png;base64,${result.pore_map}`} 
                              alt="細孔マップ"
                              className="w-full h-auto rounded"
                            />
                          ) : (
                            <div className="h-48 flex items-center justify-center bg-gray-50 rounded">
                              <p className="text-gray-500">画像が利用できません</p>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="text-sm text-gray-600 grid grid-cols-2 gap-4">
                        <div>
                          <p>データポイント数: {(result.histogram_data || []).length}</p>
                          <p>
                            範囲:{" "}
                            {result.histogram_data && result.histogram_data.length > 0
                              ? `${Math.min(...result.histogram_data.map((d) => d.diameter)).toFixed(1)} - ${Math.max(...result.histogram_data.map((d) => d.diameter)).toFixed(1)} nm`
                              : "データなし"}
                          </p>
                        </div>
                        <div>
                          <p>検出細孔数: {(result.total_pores || 0).toLocaleString()}</p>
                          <p>解析完了時刻: {new Date().toLocaleString("ja-JP")}</p>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="details" className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">解析パラメータ</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p>SEM倍率: {params.magnification}×</p>
                            <p>最大直径: {params.max_diam_nm} nm</p>
                          </div>
                          <div>
                            <p>閾値補正: {params.thresh_mag}</p>
                            <p>ピクセルサイズ: {result.pixel_size.toFixed(4)} nm/px</p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">統計情報</h4>
                        <div className="text-sm space-y-1">
                          <p>平均直径: {result.avg_diam_nm.toFixed(3)} nm</p>
                          <p>最頻直径: {result.mode_diam_nm.toFixed(3)} nm</p>
                            <p>ファイル名: {selectedFile?.name}</p>
                          <p>解析ID: {result.output_dir}</p>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>

                  <Button onClick={downloadResults} className="w-full mt-4" variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    完全な結果をダウンロード (ZIP)
                  </Button>
                </CardContent>
              </Card>
            )}

            {!result && !error && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4" />
                    <p>画像をアップロードして実際の細孔解析を実行してください</p>
                    <p className="text-sm mt-2">PoreSpyライブラリによる本格的な解析結果がここに表示されます</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
