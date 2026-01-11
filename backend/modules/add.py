import sys
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pikepdf

def create_watermark(text, pagesize, font_size=40, opacity=0.3, rotation=45):
    """Create watermark PDF page with proper orientation handling"""
    packet = io.BytesIO()
    
    # Create canvas
    c = canvas.Canvas(packet, pagesize=pagesize)
    
    # Set font
    c.setFont("Helvetica", font_size)
    
    # Use RGBA color to set opacity
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
    
    # Get page dimensions
    width, height = pagesize
    
    # Check if page is landscape (width > height)
    is_landscape = width > height
    
    # For landscape pages, we need to adjust the watermark to fit better
    if is_landscape:
        # Reduce font size for landscape pages to prevent overflow
        font_size = min(font_size, 35)
        c.setFont("Helvetica", font_size)
    
    # Calculate center position
    center_x = width / 2
    center_y = height / 2
    
    # Save current graphics state
    c.saveState()
    
    # Move to center and rotate
    c.translate(center_x, center_y)
    c.rotate(rotation)
    
    # Handle multi-line text
    if '\n' in text:
        lines = text.split('\n')
    else:
        lines = text.split('\\n')
    
    line_height = font_size + 2
    
    # Calculate total text height
    total_height = (len(lines) - 1) * line_height
    
    # Calculate maximum text width to ensure it fits within page
    max_text_width = 0
    for line in lines:
        text_width = c.stringWidth(line, "Helvetica", font_size)
        max_text_width = max(max_text_width, text_width)
    
    # For landscape pages, we need to ensure text fits within the shorter dimension (height)
    if is_landscape and max_text_width > height * 0.8:
        # If text is too wide for landscape page, reduce font size further
        scale_factor = (height * 0.8) / max_text_width
        font_size = font_size * scale_factor
        c.setFont("Helvetica", font_size)
        line_height = font_size + 2
        total_height = (len(lines) - 1) * line_height
    
    # Draw each line of text
    for i, line in enumerate(lines):
        y_offset = total_height / 2 - i * line_height
        text_width = c.stringWidth(line, "Helvetica", font_size)
        c.drawString(-text_width / 2, y_offset, line)
    
    # Restore graphics state
    c.restoreState()
    
    c.save()
    packet.seek(0)
    return packet

def add_watermark(input_pdf, output_pdf, watermark_text, font_size=40, opacity=0.3):
    try:
        # 使用pikepdf打开PDF，它会自动保留书签和链接
        print(f"Opening PDF with pikepdf...")
        pdf = pikepdf.open(input_pdf)
        
        print(f"Processing PDF, {len(pdf.pages)} pages in total.")
        
        # 收集页面方向信息
        portrait_count = 0
        landscape_count = 0
        
        # Process each page
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i + 1} ...")
            
            # Get page dimensions
            mediabox = page.MediaBox
            width = float(mediabox[2]) - float(mediabox[0])
            height = float(mediabox[3]) - float(mediabox[1])
            
            # Check page orientation
            is_landscape = width > height
            if is_landscape:
                landscape_count += 1
                print(f"  Page {i+1}: Landscape ({width:.1f}x{height:.1f})")
            else:
                portrait_count += 1
                print(f"  Page {i+1}: Portrait ({width:.1f}x{height:.1f})")
            
            # Adjust rotation for landscape pages if needed
            # Some PDFs store landscape pages as rotated portrait pages
            rotation = 0
            if '/Rotate' in page:
                rotation = page.Rotate
                print(f"  Page has rotation: {rotation} degrees")
            
            # Create watermark - pass the actual pagesize
            pagesize = (width, height)
            
            # For rotated pages, we might need to adjust
            # If page is rotated 90 or 270 degrees, dimensions are swapped
            if rotation in [90, 270]:
                # Swap width and height for rotated pages
                pagesize = (height, width)
                print(f"  Adjusted pagesize for rotation: {pagesize}")
            
            watermark_packet = create_watermark(
                watermark_text, 
                pagesize, 
                font_size=font_size, 
                opacity=opacity,
                rotation=45  # 水印自身的旋转角度
            )
            
            # 使用pikepdf将水印添加到页面
            watermark_pdf = pikepdf.open(watermark_packet)
            watermark_page = watermark_pdf.pages[0]
            
            # 将水印作为背景添加到页面
            page.add_overlay(watermark_page)
        
        # 打印页面方向统计
        print(f"\nPage orientation summary:")
        print(f"  Portrait pages: {portrait_count}")
        print(f"  Landscape pages: {landscape_count}")
        
        # 保存文件 - pikepdf会自动保留所有文档结构
        print("\nSaving output file...")
        pdf.save(output_pdf)
        
        print(f"\nCompleted. Output: {output_pdf}")
        print("Note: Document structure (bookmarks, links, metadata) has been preserved.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        # 抛出异常而不是退出进程，让调用方决定如何处理（CLI 会退出，库调用可捕获）
        raise

def main():
    # Check number of arguments
    if len(sys.argv) < 4:
        print("=" * 50)
        print("\nUsage: python add.py [Input] [Output] \"Watermark Text\" [Font Size] [Opacity]")
        print("\nArguments:")
        print("  Input:        Input PDF file path")
        print("  Output:       Output PDF file path")
        print("  Watermark:    Watermark text (use \\n for new lines)")
        print("  Font Size:    Optional - Font size (default: 40)")
        print("  Opacity:      Optional - Opacity 0.0 to 1.0 (default: 0.3)")
        print("\nExamples:")
        print("  python add.py input.pdf output.pdf \"CONFIDENTIAL\"")
        print("  python add.py input.pdf output.pdf \"DRAFT\\nDO NOT DISTRIBUTE\" 50 0.2")
        print("  python add.py input.pdf output.pdf \"SAMPLE\" 30 0.5")
        print("\nNote: This tool preserves bookmarks and internal links in the PDF.")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    watermark_text = sys.argv[3]
    
    # Set default values
    font_size = 40
    opacity = 0.3
    
    # Handle optional font size parameter
    if len(sys.argv) > 4:
        try:
            font_size = float(sys.argv[4])
            if font_size <= 0:
                print("Warning: Font size must be positive. Using default value of 40.")
                font_size = 40
        except ValueError:
            print("Warning: Font size must be a number. Using default value of 40.")
    
    # Handle optional opacity parameter
    if len(sys.argv) > 5:
        try:
            opacity = float(sys.argv[5])
            if opacity < 0 or opacity > 1:
                print("Warning: Opacity must be between 0.0 and 1.0. Using default value of 0.3.")
                opacity = 0.3
        except ValueError:
            print("Warning: Opacity must be a number. Using default value of 0.3.")
    
    # Check if input file exists
    if not os.path.exists(input_pdf):
        print(f"Error: Input file '{input_pdf}' does not exist!")
        sys.exit(1)
    
    # Check file extension
    if not input_pdf.lower().endswith('.pdf'):
        print("Error: Input file must be in PDF format!")
        sys.exit(1)
    
    print("=" * 50)
    print("PDF Watermark Tool")
    print("=" * 50)
    print(f"Input:        {input_pdf}")
    print(f"Output:       {output_pdf}")
    print(f"Watermark:    {watermark_text}")
    print(f"Font Size:    {font_size}")
    print(f"Opacity:      {opacity} ({int(opacity*100)}%)")
    print("=" * 50)
    
    # Add watermark
    add_watermark(input_pdf, output_pdf, watermark_text, font_size, opacity)

if __name__ == "__main__":
    main()