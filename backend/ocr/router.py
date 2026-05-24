from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import base64
import io
import cv2
import numpy as np
from PIL import Image

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# Initialize EasyOCR reader (cached for performance)
reader = None
_reader_error = None

def get_reader():
    """Lazy-initialize EasyOCR reader. If EasyOCR (or its dependencies) fail to
    import/initialize, cache the error and raise a RuntimeError so the caller
    can return a friendly error instead of crashing the whole app at import time.
    """
    global reader, _reader_error
    if reader is not None:
        return reader
    if _reader_error is not None:
        raise RuntimeError(f"EasyOCR initialization failed: {_reader_error}")
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        return reader
    except Exception as e:
        _reader_error = e
        raise RuntimeError(f"EasyOCR initialization failed: {e}")

class OCRRequest(BaseModel):
    image_base64: str
    doc_type: str  # 'cr', 'license', 'or'

class OCRResponse(BaseModel):
    success: bool
    text: str
    fields: dict = {}
    error: str = None

def preprocess_image_for_ocr(image_array):
    """Preprocess image for better OCR results on CR documents."""
    # Convert to grayscale if needed
    if len(image_array.shape) == 3:
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_array
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    
    # Contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Adaptive thresholding for better text detection
    thresh = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Deskew if needed
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) > 1:
        h, w = thresh.shape
        center = (w // 2, h // 2)
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(thresh, rot_matrix, (w, h), borderMode=cv2.BORDER_REFLECT)
    else:
        deskewed = thresh
    
    return deskewed

def extract_cr_fields(text):
    """Extract structured fields from CR OCR text."""
    lines = text.split('\n')
    upper_lines = [line.upper() for line in lines]
    
    fields = {
        'plate_number': '',
        'brand': '',
        'model': '',
        'color': '',
        'owner_name': ''
    }
    
    known_brands = ['HONDA', 'YAMAHA', 'SUZUKI', 'KAWASAKI', 'TOYOTA', 'NISSAN', 
                    'ISUZU', 'MITSUBISHI', 'MAZDA', 'HYUNDAI', 'KIA', 'FORD', 
                    'CHEVROLET', 'HINO']
    known_colors = ['BLACK', 'WHITE', 'RED', 'BLUE', 'GREEN', 'YELLOW', 'BROWN', 
                    'SILVER', 'GRAY', 'GREY', 'ORANGE', 'GOLD', 'MAROON', 'BEIGE']
    
    # Extract fields using label-based approach
    for i, line in enumerate(upper_lines):
        # Plate number
        if 'PLATE NO' in line or 'PLATE NUMBER' in line:
            value = line.split(':', 1)[-1].strip()
            if not value or 'PLATE' in value:
                if i + 1 < len(lines):
                    value = lines[i + 1].strip()
            fields['plate_number'] = value or fields['plate_number']
        
        # Brand
        if 'MAKE/BRAND' in line or ('MAKE' in line and 'BRAND' not in line):
            value = line.split(':', 1)[-1].strip()
            if not value or 'MAKE' in value:
                if i + 1 < len(lines):
                    value = lines[i + 1].strip()
            if value and value.upper() not in ['MAKE', 'BRAND', 'MAKE/BRAND']:
                fields['brand'] = value.upper()
            else:
                # Try to find known brand in text
                for brand in known_brands:
                    if brand in text.upper():
                        fields['brand'] = brand
                        break
        
        # Model (Year)
        if 'YEAR MODEL' in line:
            # Get the next line which should contain the year
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                # Extract 4-digit year
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', value)
                if year_match:
                    fields['model'] = year_match.group(0)
        
        # Color
        if 'COLOR' in line:
            value = line.split(':', 1)[-1].strip()
            if not value or 'COLOR' in value:
                if i + 1 < len(lines):
                    value = lines[i + 1].strip()
            if value and value.upper() not in ['COLOR']:
                fields['color'] = value.upper()
            else:
                # Try to find known color in text
                for color in known_colors:
                    if color in text.upper():
                        fields['color'] = color
                        break
        
        # Owner's name
        if "OWNER'S NAME" in line or "OWNERS NAME" in line or "OWNER NAME" in line:
            if i + 1 < len(lines):
                value = lines[i + 1].strip()
                # Clean up the name
                value = ''.join(c for c in value if c.isalpha() or c.isspace() or c == ',')
                value = ' '.join(value.split())
                if value and 'OWNER' not in value.upper():
                    fields['owner_name'] = value
    
    return fields

@router.post("/process-cr", response_model=OCRResponse)
async def process_cr_document(request: OCRRequest):
    """Process CR (Certificate of Registration) document using EasyOCR."""
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64.split(',')[-1])
        image = Image.open(io.BytesIO(image_data))
        image_array = np.array(image)
        
        # Preprocess image
        processed_image = preprocess_image_for_ocr(image_array)
        
        # Run EasyOCR
        reader_instance = get_reader()
        results = reader_instance.readtext(processed_image, detail=0)
        
        # Join results into text
        text = '\n'.join(results)
        
        # Extract structured fields
        fields = extract_cr_fields(text)
        
        return OCRResponse(
            success=True,
            text=text,
            fields=fields
        )
    
    except Exception as e:
        return OCRResponse(
            success=False,
            text="",
            fields={},
            error=str(e)
        )

@router.post("/process-document", response_model=OCRResponse)
async def process_document(request: OCRRequest):
    """Generic document processor - routes to specialized handlers."""
    if request.doc_type == 'cr':
        return await process_cr_document(request)
    else:
        # For other document types, still use Tesseract (handled on frontend)
        raise HTTPException(status_code=400, detail=f"Document type {request.doc_type} not supported by this endpoint")
