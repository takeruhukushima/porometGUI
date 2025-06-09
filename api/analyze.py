from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import porespy
import numpy as np
import matplotlib.pyplot as plt
import skimage.io
import os
import tempfile
import zipfile
from datetime import datetime
from skimage.filters import threshold_otsu
from PIL import Image
import io
import json
import traceback
import logging

# Add logging configuration at the top after imports
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poromet API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store analysis results temporarily
analysis_results = {}

# Pixel-size lookup table
PIXEL_DATA = {
    (2560, 1920): {10: 1008/5000, 20: 807/2000, 50: 1022/1000, 100: 1018/500},
    (1280, 960): {200: 406/200, 300: 303/100},
    (554, 416): {200: 174/200},
}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Poromet API is running"}

@app.post("/api/analyze")
async def analyze_pore_size(
    file: UploadFile = File(...),
    magnification: int = Form(...),
    max_diam_nm: float = Form(...),
    thresh_mag: float = Form(...)
):
    try:
        logger.info(f"Received analysis request: mag={magnification}, max_diam={max_diam_nm}, thresh={thresh_mag}")
        logger.info(f"File: {file.filename}, content_type: {file.content_type}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create temporary directory for this analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = tempfile.mkdtemp()
        out_dir = os.path.join(temp_dir, f"analysis_{timestamp}")
        os.makedirs(out_dir, exist_ok=True)
        
        logger.info(f"Created output directory: {out_dir}")
        
        # Save uploaded file
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file provided")
            
        img_path = os.path.join(temp_dir, file.filename)
        with open(img_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"Saved uploaded file: {img_path} ({len(file_content)} bytes)")
        
        # Load and process image
        try:
            img = skimage.io.imread(img_path, as_gray=True)
            h, w = img.shape[:2]
            logger.info(f"Image loaded successfully: {w}x{h}")
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to load image: {str(e)}")
        
        # Get pixel size
        try:
            px_per_nm = PIXEL_DATA[(w, h)][magnification]
        except KeyError:
            available_resolutions = list(PIXEL_DATA.keys())
            available_mags = {res: list(PIXEL_DATA[res].keys()) for res in available_resolutions}
            error_msg = f"Unknown resolution ({w}×{h}) or magnification ({magnification}×). Available combinations: {available_mags}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        nm_per_px = 1 / px_per_nm
        logger.info(f"Pixel size: {nm_per_px:.4f} nm/px")
        
        # Analysis parameters
        max_rad_px = int((max_diam_nm/2) * px_per_nm)
        if max_rad_px < 1:
            raise HTTPException(status_code=400, detail="Maximum diameter too small for this magnification")
            
        radii_px = list(range(1, max_rad_px+1))
        logger.info(f"Analysis range: 1 to {max_rad_px} pixels ({len(radii_px)} sizes)")
        
        # Segmentation
        try:
            th = threshold_otsu(img) * thresh_mag
            mask_pore = img < th
            pore_fraction = np.mean(mask_pore)
            logger.info(f"Threshold: {th:.3f}, Pore fraction: {pore_fraction:.3f}")
            
            if pore_fraction < 0.001:
                logger.warning("Very low pore fraction detected - check threshold settings")
            elif pore_fraction > 0.9:
                logger.warning("Very high pore fraction detected - check threshold settings")
                
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Image segmentation failed: {str(e)}")
        
        # Porosimetry & PSD
        try:
            logger.info("Running porosimetry analysis...")
            im_thick = porespy.filters.porosimetry(mask_pore, sizes=radii_px)
            
            logger.info("Calculating pore size distribution...")
            psd = porespy.metrics.pore_size_distribution(
                im_thick, log=False, bins=100, voxel_size=nm_per_px
            )
            
            if len(psd.bin_centers) == 0:
                raise HTTPException(status_code=500, detail="No pores detected in the analysis")
                
        except Exception as e:
            logger.error(f"Pore analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Pore size analysis failed: {str(e)}")
        
        # Statistics
        avg_rad_nm = np.average(psd.bin_centers, weights=psd.pdf)
        avg_diam_nm = 2 * avg_rad_nm
        mode_rad_nm = psd.bin_centers[np.argmax(psd.pdf)]
        mode_diam_nm = 2 * mode_rad_nm
        
        # Convert to diameter
        diam_center_nm = psd.bin_centers * 2
        diam_width_nm = psd.bin_widths * 2
        diam_pdf = psd.pdf / 2
        
        logger.info(f"Results: avg={avg_diam_nm:.2f}nm, mode={mode_diam_nm:.2f}nm")
        
        # Save results
        try:
            save_analysis_results(out_dir, img, mask_pore, im_thick, 
                                diam_center_nm, diam_width_nm, diam_pdf,
                                avg_diam_nm, mode_diam_nm, nm_per_px, 
                                w, h, magnification)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            # Continue anyway, we have the main results
        
        # Store results for download
        analysis_results[timestamp] = out_dir
        
        # Prepare response
        histogram_data = [
            {"diameter": float(d), "pdf": float(p)} 
            for d, p in zip(diam_center_nm, diam_pdf)
        ]
        
        result = {
            "avg_diam_nm": float(avg_diam_nm),
            "mode_diam_nm": float(mode_diam_nm),
            "histogram_data": histogram_data,
            "output_dir": timestamp,
            "pixel_size": float(nm_per_px)
        }
        
        logger.info("Analysis completed successfully")
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def save_analysis_results(out_dir, img, mask_pore, im_thick, 
                         diam_center_nm, diam_width_nm, diam_pdf,
                         avg_diam_nm, mode_diam_nm, nm_per_px, 
                         w, h, magnification):
    """Save all analysis results to files"""
    
    # Text report
    txt_path = os.path.join(out_dir, "pore_size_analysis.txt")
    with open(txt_path, "w") as f:
        f.write("Pore Size Analysis (all nm units)\n")
        f.write(f"Image : {w}×{h}px , {magnification}×\n")
        f.write(f"Pixel  : {nm_per_px:.4f} nm / px\n\n")
        f.write(f"Average Diameter : {avg_diam_nm:.3f} nm\n")
        f.write(f"Mode    Diameter : {mode_diam_nm:.3f} nm\n\n")
        f.write("Diameter_center(nm)\tBin_width(nm)\tPDF_diameter\n")
        for c, w_, p in zip(diam_center_nm, diam_width_nm, diam_pdf):
            f.write(f"{c:.3f}\t{w_:.3f}\t{p:.6f}\n")
    
    # Histogram plot
    plt.figure(figsize=(10, 6))
    plt.bar(diam_center_nm, diam_pdf, width=diam_width_nm, 
            edgecolor="k", alpha=0.7)
    plt.xlabel("Pore Diameter (nm)")
    plt.ylabel("Probability Density")
    plt.title("Pore Size Distribution")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "pore_size_distribution.png"), dpi=300)
    plt.close()
    
    # Raw histogram data
    raw_path = os.path.join(out_dir, "raw_histogram_data.txt")
    with open(raw_path, "w") as f:
        f.write("Diameter_center(nm)\tPDF_diameter\n")
        for c, p in zip(diam_center_nm, diam_pdf):
            f.write(f"{c:.3f}\t{p:.6f}\n")
        mean_diam_nm = np.average(diam_center_nm, weights=diam_pdf)
        f.write(f"\nWeighted Mean Diameter: {mean_diam_nm:.3f} nm\n")
    
    # Save diagnostic images
    skimage.io.imsave(os.path.join(out_dir, "thresholded_image.png"),
                     (mask_pore.astype(np.uint8) * 255))
    plt.imsave(os.path.join(out_dir, "filtered_image_colormap.png"),
               im_thick, cmap="viridis")

@app.get("/api/download/{output_dir}")
async def download_results(output_dir: str):
    """Create and return a zip file with all results"""
    try:
        if output_dir not in analysis_results:
            raise HTTPException(status_code=404, detail="Results not found")
        
        analysis_dir = analysis_results[output_dir]
        
        if not os.path.exists(analysis_dir):
            raise HTTPException(status_code=404, detail="Results directory not found")
        
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
        print(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Starting Poromet API server...")
    print("Available at: http://127.0.0.1:5328")
    print("Health check: http://127.0.0.1:5328/api/health")
    uvicorn.run(app, host="127.0.0.1", port=5328, log_level="info")
