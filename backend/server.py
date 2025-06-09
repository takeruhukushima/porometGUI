import os
import sys
import tempfile
import zipfile
import traceback
import logging
from datetime import datetime
from typing import Optional

# Auto-install missing dependencies
def install_missing_dependencies():
    """Install missing dependencies automatically"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn[standard]',
        'multipart': 'python-multipart',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'skimage': 'scikit-image',
        'PIL': 'pillow',
        'porespy': 'porespy'
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"📦 Installing missing packages: {', '.join(missing)}")
        import subprocess
        for package in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")

# Install dependencies first
install_missing_dependencies()

# Now import the required modules
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import skimage.io
from skimage.filters import threshold_otsu
from PIL import Image
import base64
from io import BytesIO
import io
import json

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

# Try to import porespy
try:
    import porespy
    PORESPY_AVAILABLE = True
    print("✅ porespy imported successfully")
except ImportError as e:
    PORESPY_AVAILABLE = False
    print(f"⚠️ porespy not available: {e}")
    print("Installing porespy...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "porespy"])
        import porespy
        PORESPY_AVAILABLE = True
        print("✅ porespy installed and imported successfully")
    except:
        print("❌ Failed to install porespy")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Poromet API",
    version="1.0.0",
    description="Pore Size Analysis API using PoreSpy"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store analysis results temporarily
analysis_results = {}

# Pixel-size lookup table (手入力データ)
PIXEL_DATA = {
    (2560, 1920): {10: 1008/5000, 20: 807/2000, 50: 1022/1000, 100: 1018/500},
    (1280, 960): {200: 406/200, 300: 303/100},
    (554, 416): {200: 174/200},
}

@app.get("/")
async def root():
    return {
        "message": "Poromet API is running",
        "status": "healthy",
        "version": "1.0.0",
        "porespy_available": PORESPY_AVAILABLE
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Poromet API is running",
        "timestamp": datetime.now().isoformat(),
        "porespy_available": PORESPY_AVAILABLE
    }

@app.post("/api/analyze")
async def analyze_pore_size(
    file: UploadFile = File(...),
    magnification: int = Form(...),
    max_diam_nm: float = Form(...),
    thresh_mag: float = Form(...)
):
    if not PORESPY_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="porespy is not available. Please install it: pip install porespy"
        )
    
    try:
        logger.info(f"解析リクエスト受信: mag={magnification}, max_diam={max_diam_nm}, thresh={thresh_mag}")
        logger.info(f"ファイル: {file.filename}, content_type: {file.content_type}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイルが提供されていません")
        
        # Create temporary directory for this analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = tempfile.mkdtemp()
        out_dir = os.path.join(temp_dir, f"analysis_{timestamp}")
        os.makedirs(out_dir, exist_ok=True)
        
        logger.info(f"出力ディレクトリ作成: {out_dir}")
        
        # Save uploaded file
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="空のファイルが提供されました")
            
        img_path = os.path.join(temp_dir, file.filename)
        with open(img_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"アップロードファイル保存: {img_path} ({len(file_content)} bytes)")
        
        # Load and process image
        try:
            img = skimage.io.imread(img_path, as_gray=True)
            h, w = img.shape[:2]
            logger.info(f"画像読み込み成功: {w}x{h}")
        except Exception as e:
            logger.error(f"画像読み込み失敗: {e}")
            raise HTTPException(status_code=400, detail=f"画像の読み込みに失敗しました: {str(e)}")
        
        # Get pixel size
        try:
            px_per_nm = PIXEL_DATA[(w, h)][magnification]
        except KeyError:
            available_resolutions = list(PIXEL_DATA.keys())
            available_mags = {res: list(PIXEL_DATA[res].keys()) for res in available_resolutions}
            error_msg = f"未知の解像度 ({w}×{h}) または倍率 ({magnification}×)。利用可能な組み合わせ: {available_mags}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        nm_per_px = 1 / px_per_nm
        logger.info(f"ピクセルサイズ: {nm_per_px:.4f} nm/px")
        
        # Analysis parameters
        max_rad_px = int((max_diam_nm/2) * px_per_nm)
        if max_rad_px < 1:
            raise HTTPException(status_code=400, detail="この倍率では最大直径が小さすぎます")
            
        radii_px = list(range(1, max_rad_px+1))
        logger.info(f"解析範囲: 1 から {max_rad_px} ピクセル ({len(radii_px)} サイズ)")
        
        # Segmentation
        try:
            th = threshold_otsu(img) * thresh_mag
            mask_pore = img < th
            pore_fraction = np.mean(mask_pore)
            logger.info(f"閾値: {th:.3f}, 細孔率: {pore_fraction:.3f}")
            
            if pore_fraction < 0.001:
                logger.warning("非常に低い細孔率が検出されました - 閾値設定を確認してください")
            elif pore_fraction > 0.9:
                logger.warning("非常に高い細孔率が検出されました - 閾値設定を確認してください")
                
        except Exception as e:
            logger.error(f"セグメンテーション失敗: {e}")
            raise HTTPException(status_code=500, detail=f"画像セグメンテーションに失敗しました: {str(e)}")
        
        # Porosimetry & PSD - 実際の細孔解析
        try:
            logger.info("細孔解析を実行中...")
            im_thick = porespy.filters.porosimetry(mask_pore, sizes=radii_px)
            
            logger.info("細孔サイズ分布を計算中...")
            psd = porespy.metrics.pore_size_distribution(
                im_thick, log=False, bins=100, voxel_size=nm_per_px
            )
            
            if len(psd.bin_centers) == 0:
                raise HTTPException(status_code=500, detail="解析で細孔が検出されませんでした")
                
        except Exception as e:
            logger.error(f"細孔解析失敗: {e}")
            raise HTTPException(status_code=500, detail=f"細孔サイズ解析に失敗しました: {str(e)}")
        
        # Statistics - 実際の統計計算
        avg_rad_nm = np.average(psd.bin_centers, weights=psd.pdf)
        avg_diam_nm = 2 * avg_rad_nm
        mode_rad_nm = psd.bin_centers[np.argmax(psd.pdf)]
        mode_diam_nm = 2 * mode_rad_nm
        
        # Convert to diameter
        diam_center_nm = psd.bin_centers * 2
        diam_width_nm = psd.bin_widths * 2
        diam_pdf = psd.pdf / 2
        
        # Count total pores (approximate)
        total_pores = int(np.sum(mask_pore) / (np.pi * (avg_rad_nm * px_per_nm)**2)) if avg_rad_nm > 0 else 0
        
        logger.info(f"解析結果: avg={avg_diam_nm:.2f}nm, mode={mode_diam_nm:.2f}nm, pores={total_pores}")
        
        # Save results
        try:
            save_analysis_results(
                out_dir, img, mask_pore, im_thick, 
                diam_center_nm, diam_width_nm, diam_pdf,
                avg_diam_nm, mode_diam_nm, nm_per_px, 
                w, h, magnification, pore_fraction, total_pores
            )
        except Exception as e:
            logger.error(f"結果保存失敗: {e}")
            # Continue anyway, we have the main results
        
        # Store results for download
        analysis_results[timestamp] = out_dir
        
        # 画像をbase64エンコードするヘルパー関数
        def image_to_base64(img, cmap='gray'):
            buffered = BytesIO()
            plt.figure(figsize=(8, 6))
            plt.imshow(img, cmap=cmap)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(buffered, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

        # ヒストグラムを生成してbase64エンコード
        def create_histogram():
            plt.figure(figsize=(10, 6))
            plt.bar(diam_center_nm, diam_pdf, width=diam_width_nm, 
                   edgecolor="k", alpha=0.7, color='steelblue')
            plt.axvline(avg_diam_nm, color='r', linestyle='--', label=f'平均: {avg_diam_nm:.1f}nm')
            plt.axvline(mode_diam_nm, color='g', linestyle='--', label=f'最頻: {mode_diam_nm:.1f}nm')
            plt.xlabel("細孔直径 (nm)", fontsize=12)
            plt.ylabel("確率密度", fontsize=12)
            plt.title("細孔サイズ分布", fontsize=14)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            buffered = BytesIO()
            plt.savefig(buffered, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

        # 画像を生成
        filtered_image = image_to_base64(mask_pore, 'gray')
        pore_map = image_to_base64(im_thick, 'viridis')
        histogram = create_histogram()

        # レスポンスデータを準備
        histogram_data = [
            {"diameter": float(d), "pdf": float(p)} 
            for d, p in zip(diam_center_nm, diam_pdf)
        ]
        
        result = {
            "avg_diam_nm": float(avg_diam_nm),
            "mode_diam_nm": float(mode_diam_nm),
            "histogram_data": histogram_data,
            "output_dir": timestamp,
            "pixel_size": float(nm_per_px),
            "pore_fraction": float(pore_fraction),
            "total_pores": int(total_pores),
            "filtered_image": filtered_image,
            "pore_map": pore_map,
            "histogram": histogram
        }
        
        logger.info("解析が正常に完了しました")
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"解析に失敗しました: {str(e)}")

def save_analysis_results(out_dir, img, mask_pore, im_thick, 
                         diam_center_nm, diam_width_nm, diam_pdf,
                         avg_diam_nm, mode_diam_nm, nm_per_px, 
                         w, h, magnification, pore_fraction, total_pores):
    """Save all analysis results to files"""
    
    # Text report
    txt_path = os.path.join(out_dir, "pore_size_analysis.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("細孔サイズ解析結果 (すべて nm 単位)\n")
        f.write("=" * 50 + "\n")
        f.write(f"画像サイズ: {w}×{h}px\n")
        f.write(f"SEM倍率: {magnification}×\n")
        f.write(f"ピクセルサイズ: {nm_per_px:.4f} nm/px\n")
        f.write(f"細孔率: {pore_fraction:.4f} ({pore_fraction*100:.2f}%)\n")
        f.write(f"検出細孔数: {total_pores}\n\n")
        f.write(f"平均直径: {avg_diam_nm:.3f} nm\n")
        f.write(f"最頻直径: {mode_diam_nm:.3f} nm\n\n")
        f.write("直径中心(nm)\t幅(nm)\tPDF\n")
        for c, w_, p in zip(diam_center_nm, diam_width_nm, diam_pdf):
            f.write(f"{c:.3f}\t{w_:.3f}\t{p:.6f}\n")
    
    # Histogram plot with Japanese labels
    plt.figure(figsize=(12, 8))
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
    plt.bar(diam_center_nm, diam_pdf, width=diam_width_nm, 
            edgecolor="k", alpha=0.7, color='steelblue')
    plt.xlabel("細孔直径 (nm)", fontsize=12)
    plt.ylabel("確率密度", fontsize=12)
    plt.title(f"細孔サイズ分布\n平均: {avg_diam_nm:.1f}nm, 最頻: {mode_diam_nm:.1f}nm", fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "pore_size_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Raw histogram data
    raw_path = os.path.join(out_dir, "raw_histogram_data.csv")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("直径中心(nm),PDF\n")
        for c, p in zip(diam_center_nm, diam_pdf):
            f.write(f"{c:.3f},{p:.6f}\n")
        f.write(f"\n# 統計情報\n")
        f.write(f"# 平均直径: {avg_diam_nm:.3f} nm\n")
        f.write(f"# 最頻直径: {mode_diam_nm:.3f} nm\n")
        f.write(f"# 細孔率: {pore_fraction:.4f}\n")
        f.write(f"# 検出細孔数: {total_pores}\n")
    
    # Save diagnostic images
    skimage.io.imsave(os.path.join(out_dir, "original_image.png"), 
                     (img * 255).astype(np.uint8))
    skimage.io.imsave(os.path.join(out_dir, "thresholded_image.png"),
                     (mask_pore.astype(np.uint8) * 255))
    
    # Save pore size map
    plt.figure(figsize=(10, 8))
    plt.imshow(im_thick, cmap="viridis")
    plt.colorbar(label="細孔サイズ (nm)")
    plt.title("細孔サイズマップ")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "pore_size_map.png"), dpi=300, bbox_inches='tight')
    plt.close()

@app.get("/api/download/{output_dir}")
async def download_results(output_dir: str):
    """Create and return a zip file with all results"""
    try:
        if output_dir not in analysis_results:
            raise HTTPException(status_code=404, detail="結果が見つかりません")
        
        analysis_dir = analysis_results[output_dir]
        
        if not os.path.exists(analysis_dir):
            raise HTTPException(status_code=404, detail="結果ディレクトリが見つかりません")
        
        # Create zip file
        zip_path = os.path.join(os.path.dirname(analysis_dir), f"poromet_results_{output_dir}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(analysis_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, analysis_dir)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"poromet_results_{output_dir}.zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ダウンロードエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ダウンロードに失敗しました: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Poromet API サーバーを起動中...")
    print("=" * 60)
    print(f"サーバーURL: http://127.0.0.1:8000")
    print(f"ヘルスチェック: http://127.0.0.1:8000/api/health")
    print(f"API ドキュメント: http://127.0.0.1:8000/docs")
    print(f"PoreSpy 利用可能: {PORESPY_AVAILABLE}")
    print("=" * 60)
    
    if not PORESPY_AVAILABLE:
        print("⚠️  警告: porespy がインストールされていません")
        print("   自動インストールを試行中...")
        print("=" * 60)
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except ImportError as e:
        print(f"❌ 依存関係エラー: {e}")
        print("次のコマンドで手動インストールしてください:")
        print("pip install fastapi uvicorn python-multipart porespy numpy matplotlib scikit-image pillow")
    except Exception as e:
        print(f"❌ サーバー起動エラー: {e}")
