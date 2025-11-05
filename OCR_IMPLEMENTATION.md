# OCR Implementation for PDF Management

## Overview
This document describes the OCR (Optical Character Recognition) implementation for processing scanned PDFs in the tutor AI system.

## Features Implemented

### Backend Components

#### 1. OCR Service (`services/ocr_service.py`)
- **Multi-engine support**: Tesseract and EasyOCR
- **Automatic detection**: Detects if PDFs are scanned or contain text
- **Image preprocessing**: Enhances image quality for better OCR results
- **Page-by-page processing**: Handles multi-page documents
- **Confidence scoring**: Provides quality metrics for OCR results
- **Multiple language support**: Italian, English, and other languages
- **Asynchronous processing**: Non-blocking OCR operations

#### 2. API Endpoints (`main.py`)
- `POST /ocr/detect-scanned` - Detect if PDF needs OCR
- `POST /ocr/process-pdf` - Process PDF with OCR
- `POST /ocr/upload-and-process` - Upload and process PDF
- `GET /ocr/engines` - Get available OCR engines
- `POST /ocr/set-engine` - Set preferred OCR engine

#### 3. Dependencies Added (`requirements.txt`)
- `pytesseract==0.3.13` - Tesseract OCR wrapper
- `easyocr==1.7.1` - EasyOCR library
- `opencv-python==4.10.0.84` - Image processing
- `numpy>=1.24.0` - Numerical computing

#### 4. Docker Configuration (`Dockerfile`)
- Tesseract OCR engine installation
- Language packs for Italian and English
- Required system dependencies for image processing

### Frontend Components

#### 1. OCR Processor (`components/OCRProcessor.tsx`)
- **Drag & drop interface** for PDF upload
- **Engine selection** with fallback support
- **Real-time processing** status
- **Results preview** with confidence metrics
- **Download functionality** for extracted text

#### 2. PDF OCR Integration (`components/PDFOCRIntegration.tsx`)
- **Automatic detection** of scanned PDFs
- **Seamless integration** with existing PDF viewer
- **Non-intrusive UI** for OCR suggestions
- **Text extraction callbacks** for further processing

#### 3. OCR Service Hook (`hooks/useAnnotationsSync.ts`)
- **Backend synchronization** for OCR results
- **Offline support** with localStorage fallback
- **Error handling** and retry mechanisms

### Testing

#### 1. Unit Tests (`test_ocr_service.py`)
- **Service initialization** tests
- **OCR engine functionality** tests
- **Image preprocessing** tests
- **PDF processing** tests
- **Scanned detection** tests
- **Error handling** tests
- **Integration tests** with real documents

## Usage

### Backend Usage

```python
from services.ocr_service import ocr_service

# Detect if PDF is scanned
detection = ocr_service.detect_scanned_pdf("path/to/pdf")

# Process with OCR if needed
if detection["is_scanned"]:
    result = ocr_service.ocr_pdf("path/to/pdf", language="ita")
    print(f"Extracted text: {result['text']}")
```

### Frontend Usage

```tsx
import { OCRProcessor } from '@/components/OCRProcessor'

function MyComponent() {
  return (
    <OCRProcessor
      onOCRComplete={(result) => {
        console.log('OCR completed:', result)
      }}
    />
  )
}
```

## Configuration

### Environment Variables
No additional environment variables required.

### Docker Configuration
The Docker setup includes:
- Tesseract OCR with Italian and English language packs
- OpenCV for image processing
- All required system dependencies

## API Response Examples

### Detection Response
```json
{
  "is_scanned": true,
  "total_pages": 10,
  "pages_with_text": 0,
  "text_percentage": 0.0,
  "avg_text_per_page": 0,
  "recommendation": "ocr"
}
```

### OCR Processing Response
```json
{
  "text": "Extracted text content...",
  "total_pages": 10,
  "processed_pages": 8,
  "average_confidence": 87.5,
  "pages_data": [...],
  "language": "ita",
  "engines_used": ["tesseract"],
  "output_file": "data/ocr_results/document_ocr.txt"
}
```

## Error Handling

### Common Errors
1. **Tesseract not available**: Falls back to EasyOCR
2. **Invalid PDF format**: Returns appropriate error message
3. **Corrupt image files**: Skips problematic pages
4. **Network issues**: Automatic retry with exponential backoff

### Error Response Format
```json
{
  "error": "Error description",
  "details": "Additional error information"
}
```

## Performance Considerations

### Optimization Features
- **Asynchronous processing**: Non-blocking operations
- **Image caching**: Avoids redundant processing
- **Selective processing**: Only processes scanned pages
- **Confidence thresholds**: Filters low-quality results

### Resource Usage
- **Memory**: Optimized for large documents
- **CPU**: Multi-threaded processing support
- **Storage**: Efficient file management

## Integration Points

### With Annotation System
- OCR results can be used for annotation creation
- Text extraction supports annotation search
- Confidence metrics help validate annotations

### With RAG System
- Extracted text can be indexed in ChromaDB
- Improves search capabilities for scanned documents
- Enables semantic search on scanned content

### With Study Planner
- OCR content can be used for study material generation
- Enables processing of scanned textbooks
- Supports automated content analysis

## Future Enhancements

### Planned Features
1. **Multi-language detection**: Automatic language identification
2. **Table extraction**: Structured data recognition
3. **Handwriting recognition**: Support for handwritten content
4. **Batch processing**: Multiple document processing
5. **Cloud OCR**: Integration with cloud OCR services

### Performance Improvements
1. **GPU acceleration**: CUDA support for faster processing
2. **Caching layer**: Redis-based result caching
3. **Queue system**: Background job processing
4. **Streaming results**: Progressive text extraction

## Troubleshooting

### Common Issues
1. **Tesseract installation**: Ensure system dependencies are installed
2. **Language packs**: Verify required language packs are available
3. **Memory usage**: Monitor memory consumption with large files
4. **Permission errors**: Check file system permissions

### Debug Commands
```bash
# Check Tesseract installation
tesseract --version

# Test OCR service
python -c "from services.ocr_service import ocr_service; print(ocr_service.tesseract_available)"

# Check available languages
tesseract --list-langs
```

## Security Considerations

### File Handling
- **Validation**: File type and size validation
- **Sandboxing**: Isolated processing environment
- **Cleanup**: Automatic file cleanup after processing

### Data Privacy
- **Local processing**: No external API calls by default
- **Temporary files**: Secure temporary file handling
- **Access control**: User-based access restrictions

## Conclusion

The OCR implementation provides a comprehensive solution for processing scanned PDFs in the tutor AI system. It offers:

- **Robust processing** with multiple engine support
- **Intelligent detection** of document types
- **Seamless integration** with existing components
- **Comprehensive testing** for reliability
- **Scalable architecture** for future enhancements

This implementation significantly enhances the system's ability to handle diverse document types and improves the overall user experience for PDF management and study material processing.